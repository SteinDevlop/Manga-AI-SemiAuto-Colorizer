"""Reconciliación y recuperación de trabajos de colorización.

Garantiza que la cola Celery y la base de datos no queden desincronizadas
(ADR-002): recupera tareas en estados intermedios tras fallos de worker,
aplica timeouts, y permite cancelación explícita. Todas las operaciones
son idempotentes.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.infrastructure.database.session import async_session_factory
from app.modules.colorization.models import ColorizationJob
from app.modules.colorization.states import (
    ACTIVE_STATES,
    ALLOWED_TRANSITIONS,
    is_terminal,
)
from sqlalchemy import select

#: Tiempo máximo permitido en estados activos antes de considerar el
#: trabajo como abandonado (para reintento o marcado como failed).
STALE_ACTIVE_TIMEOUT_SECONDS = 3600


async def find_stale_jobs(
    max_active_seconds: int = STALE_ACTIVE_TIMEOUT_SECONDS,
) -> list[dict[str, Any]]:
    """Devuelve trabajos en estados activos que parecen abandonados."""
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=max_active_seconds)
    async with async_session_factory() as session:
        stmt = select(ColorizationJob).where(
            ColorizationJob.estado.in_(tuple(ACTIVE_STATES)),
            ColorizationJob.updated_at < cutoff,
        )
        result = await session.execute(stmt)
        jobs = result.scalars().all()
        return [
            {
                "job_id": str(j.id),
                "estado": j.estado,
                "progreso": j.progreso,
                "updated_at": j.updated_at.isoformat() if j.updated_at else None,
            }
            for j in jobs
        ]


async def mark_stale_as_failed(
    max_active_seconds: int = STALE_ACTIVE_TIMEOUT_SECONDS,
) -> list[str]:
    """Marca trabajos activos abandonados como ``failed``.

    Retorna los IDs de los trabajos marcados. Es idempotente: no vuelve a
    marcar trabajos ya en estado terminal.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=max_active_seconds)
    async with async_session_factory() as session:
        stmt = select(ColorizationJob).where(
            ColorizationJob.estado.in_(tuple(ACTIVE_STATES)),
            ColorizationJob.updated_at < cutoff,
        )
        result = await session.execute(stmt)
        jobs = result.scalars().all()
        marked: list[str] = []
        for job in jobs:
            if is_terminal(job.estado):
                continue
            if "failed" not in ALLOWED_TRANSITIONS.get(job.estado, set()):
                continue
            job.estado = "failed"
            job.mensaje = "Trabajo abandonado por timeout de worker"
            job.updated_at = datetime.now(timezone.utc)
            marked.append(str(job.id))
        if marked:
            await session.commit()
        return marked


async def cancel_job(job_id: str) -> bool:
    """Cancela explícitamente un trabajo si no está en estado terminal.

    Retorna True si se canceló, False si no existía o ya era terminal.
    """
    async with async_session_factory() as session:
        stmt = select(ColorizationJob).where(ColorizationJob.id == job_id)
        result = await session.execute(stmt)
        job = result.scalar_one_or_none()
        if job is None:
            return False
        if is_terminal(job.estado):
            return False
        if "cancelled" not in ALLOWED_TRANSITIONS.get(job.estado, set()):
            return False
        job.estado = "cancelled"
        job.mensaje = "Cancelado explícitamente por el usuario"
        job.updated_at = datetime.now(timezone.utc)
        await session.commit()
        return True


async def can_transition(job_id: str, to_state: str) -> bool:
    """Retorna True si el trabajo puede transicionar a ``to_state``."""
    async with async_session_factory() as session:
        stmt = select(ColorizationJob).where(ColorizationJob.id == job_id)
        result = await session.execute(stmt)
        job = result.scalar_one_or_none()
        if job is None:
            return False
        return job.estado in ALLOWED_TRANSITIONS and to_state in ALLOWED_TRANSITIONS[job.estado]

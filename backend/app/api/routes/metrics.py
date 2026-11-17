"""Dashboard metrics endpoints.

Read-only aggregations over projects and colorization jobs. Used by the
dashboard to show real progress instead of a product description.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.infrastructure.database.session import get_session
from app.modules.colorization.repositories import ColorizationJobRepository
from app.modules.projects.models import Project
from app.modules.projects.repositories import ProjectRepository

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["metrics"])

_STAGE_ORDER = ["upload", "analysis", "character", "mask", "approve", "colorize", "export"]
_JOB_TERMINAL = {"completed", "failed", "error"}


@router.get("/metrics", response_model=Dict[str, Any])
async def get_metrics(
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """Return aggregate metrics for the dashboard."""
    logger.info("Calculando métricas del dashboard")
    try:
        project_repo = ProjectRepository(session)
        projects = await project_repo.list()

        by_status: Dict[str, int] = {}
        by_stage: Dict[str, int] = {}
        for p in projects:
            by_status[p.status] = by_status.get(p.status, 0) + 1
            by_stage[p.current_stage] = by_stage.get(p.current_stage, 0) + 1

        job_repo = ColorizationJobRepository(session)
        jobs = await job_repo.list()
        jobs_by_status: Dict[str, int] = {}
        for j in jobs:
            jobs_by_status[j.estado] = jobs_by_status.get(j.estado, 0) + 1

        active_jobs = sum(
            v for k, v in jobs_by_status.items() if k not in _JOB_TERMINAL
        )
        completed_jobs = jobs_by_status.get("completed", 0)
        failed_jobs = jobs_by_status.get("failed", 0) + jobs_by_status.get("error", 0)

        # Últimos proyectos actualizados.
        recent = sorted(
            projects,
            key=lambda p: p.updated_at or p.created_at,
            reverse=True,
        )[:5]
        recent_out = [
            {
                "id": str(p.id),
                "nombre": p.nombre,
                "current_stage": p.current_stage,
                "status": p.status,
                "portada": p.cover_image,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }
            for p in recent
        ]

        return {
            "total_proyectos": len(projects),
            "proyectos_por_estado": by_status,
            "proyectos_por_etapa": by_stage,
            "jobs": {
                "total": len(jobs),
                "activos": active_jobs,
                "completados": completed_jobs,
                "fallidos": failed_jobs,
            },
            "ultimos_proyectos": recent_out,
        }
    except Exception as exc:  # pragma: no cover - infra failure path
        logger.exception("Error al calcular métricas: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al calcular métricas.",
        )

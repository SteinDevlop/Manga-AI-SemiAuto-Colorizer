"""API routes for colorization jobs (F08 integration).

Endpoints:
* POST   /api/v1/colorizations  — create a job and enqueue real inference
* GET    /api/v1/colorizations/{job_id} — fetch job status and result
* GET    /api/v1/colorizations/{job_id}/result — serve the colorized image
"""
from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.infrastructure.database.session import get_session
from app.modules.colorization.repositories import ColorizationJobRepository
from app.modules.model_registry.repositories import ModelManifestRepository
from app.modules.page_analysis.models import Analysis
from app.modules.projects.models import Page
from app.workers.celery_app import celery_app

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/colorizations", tags=["colorizations"])


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def create_colorization(
    analysis_id: UUID,
    model_id: UUID | None = None,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Create a colorization job for an approved analysis and enqueue inference.

    The analysis must be in ``APPROVED`` state. The job is created in
    ``pending`` state and the real inference task is dispatched to the
    Celery worker queue.
    """
    analysis_uuid = analysis_id  # validado como UUID por FastAPI (422 si no lo es)
    analysis_id = str(analysis_uuid)
    logger.info("Solicitud de colorización para análisis: %s", analysis_id)
    job_repo = ColorizationJobRepository(session)

    # Resolve analysis and verify approval.
    try:
        result = await session.execute(
            select(Analysis).where(Analysis.id == analysis_uuid)
        )
        analysis = result.scalar_one_or_none()
        if analysis is None:
            logger.warning("Análisis no encontrado: %s", analysis_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found.",
            )
        if str(getattr(analysis, "estado", "")).upper() != "APPROVED":
            logger.warning("Análisis no aprobado: %s (estado: %s)", analysis_id, analysis.estado)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Analysis is not approved. Approve identities, attributes and palettes first.",
            )

        # Idempotency: return existing job if one already exists for this analysis.
        # Los trabajos fallidos/cancelados no se reutilizan: permiten reintentar.
        existing = [
            j
            for j in await job_repo.list(analysis_id=UUID(analysis_id))
            if j.estado not in ("failed", "cancelled")
        ]
        if existing:
            job = existing[-1]
            logger.info(
                "Trabajo de colorización existente encontrado: %s (estado: %s)",
                job.id,
                job.estado,
            )
            return {
                "job_id": str(job.id),
                "analysis_id": analysis_id,
                "estado": job.estado,
                "progreso": job.progreso,
                "mensaje": job.mensaje,
                "ruta_resultado": job.ruta_resultado,
                "version_modelo": job.version_modelo,
            }

        manifest_repo = ModelManifestRepository(session)
        manifests = await manifest_repo.list()
        active = [m for m in manifests if m.is_active and (m.familia or "").strip().lower() in {"colorizacion", "colorización", "colorization"}]
        if not active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={
                "code": "no_active_colorization_model",
                "message": "No hay modelos activos para colorización. Registra o activa uno en Model Registry.",
            })
        selected = next((m for m in active if m.id == model_id), None) if model_id else next((m for m in active if m.is_default), active[0])
        if selected is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={
                "code": "model_not_active",
                "message": "El modelo seleccionado no está activo o no pertenece a colorización.",
            })
        if selected.formato not in {"pt", "onnx"} or not (selected.capacidades or {}).get("ruta_archivo"):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={
                "code": "model_format_not_supported_by_pipeline",
                "message": "El pipeline de inferencia admite modelos PyTorch (.pt) y ONNX (.onnx) registrados.",
            })
        job = await job_repo.create(
            analysis_id=UUID(analysis_id),
            estado="pending",
            progreso=0,
            mensaje="Queued for colorization",
            version_modelo=selected.version,
            parametros={"model_id": str(selected.id)},
        )

        # Dispatch real inference task to the CPU worker queue.
        # send_task es síncrono (I/O con el broker): se ejecuta en un hilo para
        # no bloquear el event loop y, si el broker no responde, el trabajo se
        # marca como fallido en vez de quedar "pending" para siempre.
        try:
            await asyncio.wait_for(
                asyncio.to_thread(
                    celery_app.send_task,
                    "app.workers.tasks.colorize_page",
                    args=[str(job.id), analysis_id],
                    kwargs={"palette": {}, "model_id": str(selected.id)},
                    retry=False,
                ),
                timeout=5,
            )
        except Exception as exc:
            logger.exception("No se pudo encolar el trabajo %s: %s", job.id, exc)
            await job_repo.update(
                job.id, estado="failed", mensaje="No se pudo encolar el trabajo (broker no disponible)."
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "queue_unavailable",
                    "message": "No se pudo encolar la colorización. Verifica que Redis/Celery estén activos.",
                },
            )

        logger.info(
            "Trabajo de colorización creado: %s (análisis: %s)", job.id, analysis_id
        )
        return {
            "job_id": str(job.id),
            "analysis_id": analysis_id,
            "estado": job.estado,
            "progreso": job.progreso,
            "mensaje": job.mensaje,
        }
    except HTTPException:
        raise
    except AppError:
        raise
    except Exception as exc:  # pragma: no cover - infra failure path
        logger.exception("Error al crear trabajo de colorización: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create colorization job.",
        )


@router.get("")
async def list_colorizations(
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    """List all colorization jobs."""
    logger.info("Listando trabajos de colorización")
    try:
        job_repo = ColorizationJobRepository(session)
        jobs = await job_repo.list()
        return [
            {
                "job_id": str(job.id),
                "analysis_id": str(job.analysis_id),
                "estado": job.estado,
                "progreso": job.progreso,
                "mensaje": job.mensaje,
                "ruta_resultado": job.ruta_resultado,
                "version_modelo": job.version_modelo,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "updated_at": job.updated_at.isoformat() if job.updated_at else None,
            }
            for job in jobs
        ]
    except AppError:
        raise
    except Exception as exc:  # pragma: no cover - infra failure path
        logger.exception("Error al listar trabajos de colorización: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Failed to list colorization jobs.",
        )


@router.get("/{job_id}")
async def get_colorization(
    job_id: str = Path(..., description="Colorization job identifier"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Fetch the status and result of a colorization job."""
    logger.info("Consultando trabajo de colorización: %s", job_id)
    try:
        job_repo = ColorizationJobRepository(session)
        job = await job_repo.get(UUID(job_id))
        if job is None:
            logger.warning("Trabajo de colorización no encontrado: %s", job_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Colorization job not found.",
            )
        return {
            "job_id": str(job.id),
            "analysis_id": str(job.analysis_id),
            "estado": job.estado,
            "progreso": job.progreso,
            "mensaje": job.mensaje,
            "ruta_resultado": job.ruta_resultado,
            "version_modelo": job.version_modelo,
            "parametros": job.parametros,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        }
    except HTTPException:
        raise
    except AppError:
        raise
    except Exception as exc:  # pragma: no cover - infra failure path
        logger.exception("Error al consultar trabajo %s: %s", job_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Failed to read colorization job.",
        )


@router.get("/{job_id}/result")
async def get_colorization_result(
    job_id: str = Path(..., description="Colorization job identifier"),
    session: AsyncSession = Depends(get_session),
):
    """Serve the colorized result image for a completed job."""
    logger.info("Solicitando resultado de colorización: %s", job_id)
    try:
        job_repo = ColorizationJobRepository(session)
        job = await job_repo.get(UUID(job_id))
        if job is None:
            logger.warning("Trabajo de colorización no encontrado: %s", job_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Colorization job not found.",
            )
        if not job.ruta_resultado:
            logger.warning("Resultado no disponible para trabajo: %s", job_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No result available for this job.",
            )
        return FileResponse(path=job.ruta_resultado, media_type="image/png")
    except HTTPException:
        raise
    except AppError:
        raise
    except Exception as exc:  # pragma: no cover - infra failure path
        logger.exception("Error al servir resultado %s: %s", job_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Failed to serve result.",
        )

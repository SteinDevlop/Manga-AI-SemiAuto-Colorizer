"""API routes for projects (F08 integration).

Endpoints:
* GET    /api/v1/projects  — list projects
* POST   /api/v1/projects  — create a new project
"""
from __future__ import annotations

from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.create_project import (
    CreateProjectInput,
    CreateProjectUseCase,
)
from app.core.logging import get_logger
from app.infrastructure.database.session import get_session
from app.modules.page_analysis.models import Analysis
from app.modules.page_analysis.repositories import AnalysisRepository, PageRepository
from app.modules.projects.models import Project
from app.modules.projects.repositories import ProjectRepository

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])

_STAGE_ORDER = ["upload", "analysis", "character", "mask", "approve", "colorize", "export"]


def _progress_percentage(stage_progress: Optional[list]) -> int:
    if not stage_progress:
        return 0
    done = len([s for s in stage_progress if s in _STAGE_ORDER])
    return int(round(done / len(_STAGE_ORDER) * 100))


@router.get("", response_model=List[dict[str, Any]])
async def list_projects(
    session: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    estado: Optional[str] = Query(None, description="Filter by project status"),
    current_stage: Optional[str] = Query(None, description="Filter by current stage"),
) -> List[dict[str, Any]]:
    """List projects with pagination and optional status/stage filters."""
    try:
        repo = ProjectRepository(session)
        stmt = select(Project).order_by(desc(Project.created_at))
        if estado:
            stmt = stmt.where(Project.status == estado)
        if current_stage:
            stmt = stmt.where(Project.current_stage == current_stage)

        total_result = await session.execute(select(func.count()).select_from(stmt.subquery()))
        total = total_result.scalar_one()

        stmt = stmt.offset((page - 1) * size).limit(size)
        result = await session.execute(stmt)
        projects = result.scalars().all()

        return [
            {
                "id": str(p.id),
                "nombre": p.nombre,
                "descripcion": p.descripcion,
                "tipo": None,
                "portada": p.cover_image,
                "current_stage": p.current_stage,
                "status": p.status,
                "progreso": _progress_percentage(p.stage_progress),
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
                "total": total,
                "page": page,
                "size": size,
            }
            for p in projects
        ]
    except Exception as exc:  # pragma: no cover - infra failure path
        logger.exception("Error al listar proyectos: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al listar proyectos.",
        )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=dict[str, Any])
async def create_project(
    payload: dict[str, Any],
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Create a new project with a unique name."""
    logger.info("Creando nuevo proyecto")
    try:
        nombre = payload.get("nombre")
        if not nombre or not isinstance(nombre, str) or not nombre.strip():
            logger.warning("Intento de crear proyecto sin nombre válido")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El campo 'nombre' es requerido.",
            )

        descripcion = payload.get("descripcion")
        if descripcion is not None and not isinstance(descripcion, str):
            logger.warning("Descripción inválida: %s", type(descripcion).__name__)
            descripcion = None

        use_case = CreateProjectUseCase(ProjectRepository(session))
        result = await use_case.execute(
            CreateProjectInput(
                nombre=nombre.strip(),
                descripcion=descripcion.strip() if descripcion else None,
            )
        )
        logger.info("Proyecto creado exitosamente: %s", result.id)
        return {
            "id": result.id,
            "nombre": result.nombre,
            "descripcion": result.descripcion,
            "created_at": result.created_at,
        }
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - infra failure path
        logger.exception("Error al crear proyecto: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc) or "No se pudo crear el proyecto.",
        )


@router.get("/{project_id}", response_model=dict[str, Any])
async def get_project(
    project_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get a project with its pages, current stage and the active analysis id."""
    logger.info("Obteniendo proyecto: %s", project_id)
    try:
        repo = ProjectRepository(session)
        project = await repo.get(UUID(project_id))
        if project is None:
            logger.warning("Proyecto no encontrado: %s", project_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found.",
            )

        page_repo = PageRepository(session)
        pages = await page_repo.list(project_id=UUID(project_id))

        pages_out = []
        for page in pages:
            # Active analysis = most recent analysis for the page (handles the
            # case where a page is re-analyzed and keeps several analyses).
            stmt = (
                select(Analysis)
                .where(Analysis.page_id == page.id)
                .order_by(desc(Analysis.created_at))
                .limit(1)
            )
            analysis_result = await session.execute(stmt)
            analysis = analysis_result.scalar_one_or_none()
            pages_out.append(
                {
                    "page_id": str(page.id),
                    "nombre_archivo_original": page.nombre_archivo_original,
                    "ruta_archivo": page.ruta_archivo,
                    "estado": page.estado,
                    "analysis_id": str(analysis.id) if analysis else None,
                    "analysis_estado": analysis.estado if analysis else None,
                    "created_at": page.created_at.isoformat() if page.created_at else None,
                }
            )

        return {
            "id": str(project.id),
            "nombre": project.nombre,
            "descripcion": project.descripcion,
            "tipo": None,
            "portada": project.cover_image,
            "current_stage": project.current_stage,
            "status": project.status,
            "stage_progress": project.stage_progress or [],
            "progreso": _progress_percentage(project.stage_progress),
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
            "pages": pages_out,
        }
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - infra failure path
        logger.exception("Error al obtener proyecto %s: %s", project_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener el proyecto.",
        )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a project by its ID."""
    logger.info("Eliminando proyecto: %s", project_id)
    try:
        repo = ProjectRepository(session)
        deleted = await repo.delete(project_id)
        if not deleted:
            logger.warning("Proyecto no encontrado: %s", project_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found.",
            )
        logger.info("Proyecto eliminado exitosamente: %s", project_id)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - infra failure path
        logger.exception("Error al eliminar proyecto: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al eliminar proyecto.",
        )


@router.patch("/{project_id}/stage", response_model=dict[str, Any])
async def transition_stage(
    project_id: str,
    payload: dict[str, Any],
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Transition the current stage of a project with validation rules.

    Rules:
      * Cannot advance without completing the previous stage.
      * Cannot return to ``upload`` once completed.
      * Regressions are allowed from ``analysis`` onward only.
    """
    logger.info("Transición de etapa para proyecto: %s", project_id)
    try:
        repo = ProjectRepository(session)
        project = await repo.get(UUID(project_id))
        if project is None:
            logger.warning("Proyecto no encontrado: %s", project_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found.",
            )

        action = payload.get("action")
        stage = payload.get("stage")
        if action not in ("complete", "regress"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "invalid_action",
                    "message": "Acción inválida. Use 'complete' o 'regress'.",
                },
            )
        if not isinstance(stage, str) or stage not in _STAGE_ORDER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "invalid_stage",
                    "message": f"Etapa inválida: {stage}. Debe ser una de {_STAGE_ORDER}.",
                },
            )

        progress = list(project.stage_progress or [])
        current_idx = _STAGE_ORDER.index(project.current_stage)
        target_idx = _STAGE_ORDER.index(stage)

        if action == "complete":
            # No volver a completar upload una vez completada (no retornable).
            if stage == "upload" and stage in progress:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "upload_not_returnable",
                        "message": "Upload ya está completada y no puede volver a abrirse.",
                    },
                )
            # No se puede completar una etapa sin haber completado las previas.
            required_previous = _STAGE_ORDER[:target_idx]
            missing = [s for s in required_previous if s not in progress]
            if missing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "stage_out_of_order",
                        "message": f"Debe completar antes: {', '.join(missing)}.",
                    },
                )
            if stage not in progress:
                progress.append(stage)
            # Si se completa la etapa actual, avanzar a la siguiente pendiente.
            new_current = project.current_stage
            if stage == project.current_stage:
                following = [s for s in _STAGE_ORDER[current_idx + 1:] if s not in progress]
                new_current = following[0] if following else project.current_stage
            # Si se completó todo, marcar como completado.
            if all(s in progress for s in _STAGE_ORDER):
                new_status = "completado"
            else:
                new_status = "en_progreso"
            updated = await repo.update(
                UUID(project_id),
                current_stage=new_current,
                status=new_status,
                stage_progress=progress,
            )
            accion = "completada"
        else:  # regress
            if project.current_stage == "upload":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "upload_not_returnable",
                        "message": "Upload no es retornable una vez iniciada.",
                    },
                )
            if stage == "upload":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "upload_not_returnable",
                        "message": "No se puede retroceder a Upload una vez completada.",
                    },
                )
            # Solo se puede retroceder a una etapa completada y previa.
            if stage not in progress:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "stage_not_completed",
                        "message": f"La etapa '{stage}' no está completada.",
                    },
                )
            if target_idx >= current_idx:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "cannot_regress_forward",
                        "message": "Solo se puede retroceder a una etapa previa.",
                    },
                )
            # Retrocesos permitidos desde analysis en adelante (índice >= 1).
            if current_idx < 1:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "regress_not_allowed",
                        "message": "La retrocesión solo está permitida desde Analysis en adelante.",
                    },
                )
            updated = await repo.update(
                UUID(project_id),
                current_stage=stage,
                status="en_progreso",
                stage_progress=progress,
            )
            new_current = stage
            new_status = "en_progreso"
            accion = "retrocedida"

        return {
            "project_id": str(updated.id),
            "action": accion,
            "stage": stage,
            "current_stage": updated.current_stage,
            "status": updated.status,
            "stage_progress": updated.stage_progress or [],
            "progreso": _progress_percentage(updated.stage_progress),
        }
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - infra failure path
        logger.exception("Error al transicionar etapa %s: %s", project_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al transicionar la etapa.",
        )

"""API routes for page analysis (F08 integration).

Endpoints:
* POST   /api/v1/analysis/{page_id}  — run panel/character/mask analysis
* GET    /api/v1/analysis/{analysis_id} — get analysis result
* POST   /api/v1/analysis/{analysis_id}/approve — approve analysis for colorization
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path as PathParam, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_engine.adapters.mock.character_detector import MockCharacterDetector
from app.ai_engine.adapters.mock.panel_detector import MockPanelDetector
from app.ai_engine.adapters.mock.segmenter import MockSegmenter
from app.application.use_cases.analyze_page import AnalyzePageUseCase
from app.application.use_cases.approve_analysis import ApproveAnalysisInput, ApproveAnalysisUseCase
from app.application.use_cases.get_analysis import GetAnalysisInput, GetAnalysisUseCase
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.infrastructure.database.session import get_session
from app.infrastructure.storage.service import StorageService
from app.modules.character_analysis.repositories import CharacterAppearanceRepository, CharacterRepository
from app.modules.colorization.repositories import MaskArtifactRepository
from app.modules.page_analysis.repositories import (
    AnalysisRepository,
    PageRepository,
    PanelRepository,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


@router.post("/{page_id}", status_code=status.HTTP_200_OK)
async def analyze_page(
    page_id: str = PathParam(..., description="Page identifier"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Run panel, character and mask analysis on a page.

    Uses mock AI adapters (no heavy inference). Persists panels, characters,
    appearances and mask artifacts, and creates/updates the analysis record.
    Returns the analysis result.
    """
    logger.info("Iniciando análisis de página: %s", page_id)
    page_repo = PageRepository(session)
    page = await page_repo.get(UUID(page_id))
    if page is None:
        logger.warning("Página no encontrada: %s", page_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found.",
        )

    use_case = AnalyzePageUseCase(
        page_repository=page_repo,
        panel_repository=PanelRepository(session),
        character_repository=CharacterRepository(session),
        character_appearance_repository=CharacterAppearanceRepository(session),
        analysis_repository=AnalysisRepository(session),
        mask_artifact_repository=MaskArtifactRepository(session),
        storage_service=StorageService(),
        panel_detector=MockPanelDetector(),
        character_detector=MockCharacterDetector(),
        segmenter=MockSegmenter(),
    )

    try:
        result = await use_case.execute(
            __import__(
                "app.application.use_cases.analyze_page", fromlist=["AnalyzePageInput"]
            ).AnalyzePageInput(page_id=UUID(page_id))
        )
        logger.info(
            "Análisis completado: %s (página: %s, paneles: %d, personajes: %d)",
            result.analysis_id,
            page_id,
            len(result.panels),
            len(result.characters),
        )
        return {
            "analysis_id": result.analysis_id,
            "page_id": result.page_id,
            "estado": result.estado,
            "confianza_global": result.confianza_global,
            "version_modelo": result.version_modelo,
            "panels": [
                {
                    "id": p.id,
                    "page_id": p.page_id,
                    "numero_orden": p.numero_orden,
                    "x": p.x,
                    "y": p.y,
                    "ancho": p.ancho,
                    "alto": p.alto,
                    "confianza_deteccion": p.confianza_deteccion,
                }
                for p in result.panels
            ],
            "characters": [
                {
                    "id": c.id,
                    "nombre": c.nombre,
                    "confianza_identidad": c.confianza_identidad,
                }
                for c in result.characters
            ],
            "appearances": [
                {
                    "id": a.id,
                    "page_id": a.page_id,
                    "character_id": a.character_id,
                    "panel_id": a.panel_id,
                    "confianza_deteccion": a.confianza_deteccion,
                }
                for a in result.appearances
            ],
            "masks": [
                {
                    "id": m.id,
                    "appearance_id": m.appearance_id,
                    "tipo_mascara": m.tipo_mascara,
                    "ruta_archivo": m.ruta_archivo,
                    "hash_sha256": m.hash_sha256,
                    "ancho": m.ancho,
                    "alto": m.alto,
                }
                for m in result.masks
            ],
        }
    except NotFoundError as exc:
        logger.error("Página no encontrada en análisis: %s", exc.message)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        )
    except Exception as exc:  # pragma: no cover - infra failure path
        logger.exception("Error al analizar página %s: %s", page_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Analysis failed.",
        )


@router.get("/{analysis_id}")
async def get_analysis(
    analysis_id: str = PathParam(..., description="Analysis identifier"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get an analysis result with panels, characters, appearances and masks."""
    logger.info("Obteniendo análisis: %s", analysis_id)
    try:
        use_case = GetAnalysisUseCase(
            analysis_repository=AnalysisRepository(session),
            panel_repository=PanelRepository(session),
            character_repository=CharacterRepository(session),
            character_appearance_repository=CharacterAppearanceRepository(session),
            mask_artifact_repository=MaskArtifactRepository(session),
        )

        result = await use_case.execute(
            __import__(
                "app.application.use_cases.get_analysis", fromlist=["GetAnalysisInput"]
            ).GetAnalysisInput(analysis_id=UUID(analysis_id))
        )
        logger.info("Análisis obtenido: %s", analysis_id)
        return {
            "analysis_id": result.analysis_id,
            "page_id": result.page_id,
            "estado": result.estado,
            "confianza_global": result.confianza_global,
            "version_modelo": result.version_modelo,
            "panels": [
                {
                    "id": p.id,
                    "page_id": p.page_id,
                    "numero_orden": p.numero_orden,
                    "x": p.x,
                    "y": p.y,
                    "ancho": p.ancho,
                    "alto": p.alto,
                    "confianza_deteccion": p.confianza_deteccion,
                }
                for p in result.panels
            ],
            "characters": [
                {
                    "id": c.id,
                    "nombre": c.nombre,
                    "descripcion": c.descripcion,
                    "confianza_identidad": c.confianza_identidad,
                }
                for c in result.characters
            ],
            "appearances": [
                {
                    "id": a.id,
                    "page_id": a.page_id,
                    "character_id": a.character_id,
                    "panel_id": a.panel_id,
                    "confianza_deteccion": a.confianza_deteccion,
                }
                for a in result.appearances
            ],
            "masks": [
                {
                    "id": m.id,
                    "appearance_id": m.appearance_id,
                    "tipo_mascara": m.tipo_mascara,
                    "ruta_archivo": m.ruta_archivo,
                    "hash_sha256": m.hash_sha256,
                    "ancho": m.ancho,
                    "alto": m.alto,
                }
                for m in result.masks
            ],
        }
    except NotFoundError as exc:
        logger.error("Análisis no encontrado: %s", exc.message)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        )
    except Exception as exc:  # pragma: no cover - infra failure path
        logger.exception("Error al obtener análisis %s: %s", analysis_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Failed to read analysis.",
        )


@router.post("/{analysis_id}/approve", status_code=status.HTTP_200_OK)
async def approve_analysis(
    analysis_id: str = PathParam(..., description="Analysis identifier"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Approve a page analysis so a colorization job can be created.

    Human-in-the-loop: no colorization job can be created without approval.
    """
    logger.info("Aprobando análisis: %s", analysis_id)
    use_case = ApproveAnalysisUseCase(AnalysisRepository(session))

    try:
        result = await use_case.execute(
            ApproveAnalysisInput(analysis_id=UUID(analysis_id))
        )
        logger.info(
            "Análisis aprobado: %s (estado: %s)",
            analysis_id,
            result.estado,
        )
        return {
            "analysis_id": result.analysis_id,
            "estado": result.estado,
        }
    except NotFoundError as exc:
        logger.error("Análisis no encontrado para aprobación: %s", exc.message)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        )
    except Exception as exc:  # pragma: no cover - infra failure path
        logger.exception("Error al aprobar análisis %s: %s", analysis_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Failed to approve analysis.",
        )

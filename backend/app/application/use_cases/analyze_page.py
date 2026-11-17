"""Page analysis use case.

Orchestrates panel detection, character detection per panel, mask
segmentation, and persistence of panels, appearances and mask artifacts,
updating the analysis state. Depends on ai_engine Protocol adapters,
never on concrete AI implementations.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from app.ai_engine.contracts import CharacterDetector, PanelDetector, Segmenter
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger

logger = get_logger(__name__)


class PageRepository(Protocol):
    """Port for page read operations."""

    async def get(
        self, *, page_id: UUID
    ) -> object | None:  # pragma: no cover - protocol stub
        """Return the page with the given ID, or None when not found."""
        ...


class PanelRepository(Protocol):
    """Port for panel persistence operations."""

    async def create(  # pragma: no cover - protocol stub
        self,
        *,
        page_id: UUID,
        numero_orden: int,
        x: float,
        y: float,
        ancho: float,
        alto: float,
        confianza_deteccion: float | None,
    ) -> object:
        """Create and persist a panel, returning the persisted entity."""
        ...


class CharacterRepository(Protocol):
    """Port for character persistence operations."""

    async def create(  # pragma: no cover - protocol stub
        self,
        *,
        nombre: str,
        descripcion: str | None = None,
        confianza_identidad: float | None,
    ) -> object:
        """Create and persist a character, returning the persisted entity."""
        ...


class CharacterAppearanceRepository(Protocol):
    """Port for character appearance persistence operations."""

    async def create(  # pragma: no cover - protocol stub
        self,
        *,
        page_id: UUID,
        character_id: UUID,
        panel_id: UUID | None,
        confianza_deteccion: float | None,
    ) -> object:
        """Create and persist a character appearance, returning the entity."""
        ...


class AnalysisRepository(Protocol):
    """Port for analysis persistence operations."""

    async def get_by_page_id(
        self, *, page_id: UUID
    ) -> object | None:  # pragma: no cover - protocol stub
        """Return the analysis for the given page, or None when not found."""
        ...

    async def create(  # pragma: no cover - protocol stub
        self,
        *,
        page_id: UUID,
        estado: str,
        confianza_global: float | None,
        version_modelo: str | None,
    ) -> object:
        """Create and persist an analysis, returning the persisted entity."""
        ...

    async def update(  # pragma: no cover - protocol stub
        self,
        *,
        analysis_id: UUID,
        estado: str | None = None,
        confianza_global: float | None,
        version_modelo: str | None,
    ) -> object | None:
        """Update analysis fields, returning the persisted entity or None."""
        ...


class MaskArtifactRepository(Protocol):
    """Port for mask artifact persistence operations."""

    async def create(  # pragma: no cover - protocol stub
        self,
        *,
        appearance_id: UUID,
        tipo_mascara: str,
        ruta_archivo: str,
        hash_sha256: str,
        ancho: int | None,
        alto: int | None,
    ) -> object:
        """Create and persist a mask artifact, returning the persisted entity."""
        ...


class StorageService(Protocol):
    """Port for artifact storage operations."""

    def save(  # pragma: no cover - protocol stub
        self,
        *,
        source_path: str,
        artifact_type: str,
        original_name: str | None,
    ) -> dict[str, Any]:
        """Save a file and return artifact metadata."""
        ...


@dataclass(frozen=True)
class AnalyzePageInput:
    """Input data for analyzing a page."""

    page_id: UUID


@dataclass(frozen=True)
class PanelOutput:
    """Simple output DTO for a detected panel, never an ORM model."""

    id: str
    page_id: str
    numero_orden: int
    x: float
    y: float
    ancho: float
    alto: float
    confianza_deteccion: float | None


@dataclass(frozen=True)
class CharacterOutput:
    """Simple output DTO for a detected character, never an ORM model."""

    id: str
    nombre: str
    confianza_identidad: float | None


@dataclass(frozen=True)
class CharacterAppearanceOutput:
    """Simple output DTO for a character appearance, never an ORM model."""

    id: str
    page_id: str
    character_id: str
    panel_id: str | None
    confianza_deteccion: float | None


@dataclass(frozen=True)
class MaskArtifactOutput:
    """Simple output DTO for a mask artifact, never an ORM model."""

    id: str
    appearance_id: str
    tipo_mascara: str
    ruta_archivo: str
    hash_sha256: str
    ancho: int | None
    alto: int | None


@dataclass(frozen=True)
class AnalyzePageOutput:
    """Simple output DTO for page analysis results, never ORM models."""

    analysis_id: str
    page_id: str
    estado: str
    confianza_global: float | None
    version_modelo: str | None
    panels: list[PanelOutput]
    characters: list[CharacterOutput]
    appearances: list[CharacterAppearanceOutput]
    masks: list[MaskArtifactOutput]


class AnalyzePageUseCase:
    """Analyze a manga page: panels, characters, masks and analysis state.

    Orchestrates the PanelDetector, CharacterDetector and Segmenter Protocol
    adapters, persists panels, characters, appearances and mask artifacts through
    injected repository ports, stores mask files through the storage service, and
    updates the analysis state. No heavy inference runs here; adapters are
    mocks in this phase.
    """

    def __init__(
        self,
        *,
        page_repository: PageRepository,
        panel_repository: PanelRepository,
        character_repository: CharacterRepository,
        character_appearance_repository: CharacterAppearanceRepository,
        analysis_repository: AnalysisRepository,
        mask_artifact_repository: MaskArtifactRepository,
        storage_service: StorageService,
        panel_detector: PanelDetector,
        character_detector: CharacterDetector,
        segmenter: Segmenter,
    ) -> None:
        self._page_repository = page_repository
        self._panel_repository = panel_repository
        self._character_repository = character_repository
        self._character_appearance_repository = character_appearance_repository
        self._analysis_repository = analysis_repository
        self._mask_artifact_repository = mask_artifact_repository
        self._storage_service = storage_service
        self._panel_detector = panel_detector
        self._character_detector = character_detector
        self._segmenter = segmenter

    async def execute(self, input_data: AnalyzePageInput) -> AnalyzePageOutput:
        """Execute the page analysis use case.

        Raises:
            NotFoundError: when no page matches the given page_id.
        """
        try:
            page = await self._page_repository.get(page_id=input_data.page_id)
            if page is None:
                logger.warning("Página no encontrada para análisis: %s", input_data.page_id)
                raise NotFoundError(
                    message="Page not found.",
                    details={"field": "page_id", "reason": "not_found"},
                )

            image_path = str(page.ruta_archivo)

            # 1. Detect panels (S2).
            panel_detections = self._panel_detector.detect(image_path, min_confidence=0.0)

            panels_output: list[PanelOutput] = []
            panel_entities: list[object] = []
            for detection in panel_detections:
                panel_entity = await self._panel_repository.create(
                    page_id=input_data.page_id,
                    numero_orden=int(detection["numero_orden"]),
                    x=float(detection["x"]),
                    y=float(detection["y"]),
                    ancho=float(detection["ancho"]),
                    alto=float(detection["alto"]),
                    confianza_deteccion=float(detection.get("confianza", 0.0)),
                )
                panel_entities.append(panel_entity)
                panels_output.append(
                    PanelOutput(
                        id=str(panel_entity.id),
                        page_id=str(input_data.page_id),
                        numero_orden=int(detection["numero_orden"]),
                        x=float(detection["x"]),
                        y=float(detection["y"]),
                        ancho=float(detection["ancho"]),
                        alto=float(detection["alto"]),
                        confianza_deteccion=float(detection.get("confianza", 0.0)),
                    )
                )

            # 2. Detect characters per panel (S3).
            characters_output: list[CharacterOutput] = []
            appearances_output: list[CharacterAppearanceOutput] = []
            appearance_entities: list[object] = []
            all_character_detections: list[dict] = []

            for panel_entity in panel_entities:
                character_detections = self._character_detector.detect(image_path, min_confidence=0.0)
                all_character_detections.extend(character_detections)

                for detection in character_detections:
                    character_entity = await self._character_repository.create(
                        nombre=str(detection.get("etiqueta", "character")),
                        descripcion=None,
                        confianza_identidad=float(detection.get("confianza", 0.0)),
                    )
                    appearance_entity = await self._character_appearance_repository.create(
                        page_id=input_data.page_id,
                        character_id=character_entity.id,
                        panel_id=panel_entity.id,
                        confianza_deteccion=float(detection.get("confianza", 0.0)),
                    )
                    appearance_entities.append(appearance_entity)
                    characters_output.append(
                        CharacterOutput(
                            id=str(character_entity.id),
                            nombre=str(detection.get("etiqueta", "character")),
                            confianza_identidad=float(detection.get("confianza", 0.0)),
                        )
                    )
                    appearances_output.append(
                        CharacterAppearanceOutput(
                            id=str(appearance_entity.id),
                            page_id=str(input_data.page_id),
                            character_id=str(character_entity.id),
                            panel_id=str(panel_entity.id),
                            confianza_deteccion=float(detection.get("confianza", 0.0)),
                        )
                    )

            # 3. Segment masks per appearance (S5).
            masks_output: list[MaskArtifactOutput] = []
            for appearance_entity in appearance_entities:
                mask_detections = self._segmenter.segment(
                    image_path,
                    regions=[
                        {
                            "region_id": str(appearance_entity.id),
                            "x": float(detection.get("x", 0.0)),
                            "y": float(detection.get("y", 0.0)),
                            "ancho": float(detection.get("ancho", 0.0)),
                            "alto": float(detection.get("alto", 0.0)),
                        }
                        for detection in all_character_detections
                    ],
                )

                for mask_detection in mask_detections:
                    saved = self._storage_service.save(
                        source_path=str(mask_detection["ruta_archivo"]),
                        artifact_type="mask",
                        original_name=None,
                    )
                    mask_entity = await self._mask_artifact_repository.create(
                        appearance_id=appearance_entity.id,
                        tipo_mascara=str(mask_detection.get("tipo_mascara", "character")),
                        ruta_archivo=str(saved["ruta_archivo"]),
                        hash_sha256=str(saved["hash_sha256"]),
                        ancho=mask_detection.get("ancho"),
                        alto=mask_detection.get("alto"),
                    )
                    masks_output.append(
                        MaskArtifactOutput(
                            id=str(mask_entity.id),
                            appearance_id=str(mask_entity.appearance_id),
                            tipo_mascara=str(mask_detection.get("tipo_mascara", "character")),
                            ruta_archivo=str(saved["ruta_archivo"]),
                            hash_sha256=str(saved["hash_sha256"]),
                            ancho=mask_detection.get("ancho"),
                            alto=mask_detection.get("alto"),
                        )
                    )

            # 4. Update or create the analysis record.
            analysis = await self._analysis_repository.get_by_page_id(page_id=input_data.page_id)
            if analysis is None:
                analysis = await self._analysis_repository.create(
                    page_id=input_data.page_id,
                    estado="analysis_completed",
                    confianza_global=0.0,
                    version_modelo="mock-v1",
                )
            else:
                analysis = await self._analysis_repository.update(
                    analysis_id=analysis.id,
                    estado="analysis_completed",
                    confianza_global=0.0,
                    version_modelo="mock-v1",
                )

            logger.info(
                "Análisis completado: %s (página: %s, paneles: %d, personajes: %d, máscaras: %d)",
                analysis.id,
                input_data.page_id,
                len(panels_output),
                len(characters_output),
                len(masks_output),
            )

            return AnalyzePageOutput(
                analysis_id=str(analysis.id),
                page_id=str(input_data.page_id),
                estado=str(analysis.estado),
                confianza_global=analysis.confianza_global,
                version_modelo=analysis.version_modelo,
                panels=panels_output,
                characters=characters_output,
                appearances=appearances_output,
                masks=masks_output,
            )
        except NotFoundError:
            raise
        except Exception as exc:  # pragma: no cover - infra failure path
            logger.exception(
                "Error al analizar página %s: %s", input_data.page_id, exc
            )
            raise

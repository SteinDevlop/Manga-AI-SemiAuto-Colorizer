"""Get analysis use case.

Returns an analysis with its panels, characters, appearances and masks,
or raises NotFoundError when missing. Depends on repository ports,
never on concrete ORM models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from app.core.exceptions import NotFoundError


class AnalysisRepository(Protocol):
    """Port for analysis read operations."""

    async def get(self, *, analysis_id: UUID) -> object | None:  # pragma: no cover - protocol stub
        """Return the analysis with the given ID, or None when not found."""
        ...


class PanelRepository(Protocol):
    """Port for panel read operations."""

    async def list(  # pragma: no cover - protocol stub
        self,
        *,
        page_id: UUID | None = None,
    ) -> list[object]:
        """Return panels, optionally filtered by page id."""
        ...


class CharacterRepository(Protocol):
    """Port for character read operations."""

    async def get(self, *, character_id: UUID) -> object | None:  # pragma: no cover - protocol stub
        """Return the character with the given ID, or None when not found."""
        ...


class CharacterAppearanceRepository(Protocol):
    """Port for character appearance read operations."""

    async def list(  # pragma: no cover - protocol stub
        self,
        *,
        page_id: UUID | None = None,
        character_id: UUID | None = None,
    ) -> list[object]:
        """Return appearances, optionally filtered by page/character id."""
        ...


class MaskArtifactRepository(Protocol):
    """Port for mask artifact read operations."""

    async def list(  # pragma: no cover - protocol stub
        self,
        *,
        appearance_id: UUID | None = None,
    ) -> list[object]:
        """Return mask artifacts, optionally filtered by appearance id."""
        ...


@dataclass(frozen=True)
class GetAnalysisInput:
    """Input data for getting an analysis."""

    analysis_id: UUID


@dataclass(frozen=True)
class PanelOutput:
    """Simple output DTO for a panel, never an ORM model."""

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
    """Simple output DTO for a character, never an ORM model."""

    id: str
    nombre: str
    descripcion: str | None
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
class GetAnalysisOutput:
    """Simple output DTO for an analysis and its relations, never ORM models."""

    analysis_id: str
    page_id: str
    estado: str
    confianza_global: float | None
    version_modelo: str | None
    panels: list[PanelOutput]
    characters: list[CharacterOutput]
    appearances: list[CharacterAppearanceOutput]
    masks: list[MaskArtifactOutput]


class GetAnalysisUseCase:
    """Retrieve an analysis with its panels, characters, appearances and masks.

    Depends on repository ports only; returns frozen DTOs, never ORM models.
    Raises NotFoundError when the analysis does not exist.
    """

    def __init__(
        self,
        *,
        analysis_repository: AnalysisRepository,
        panel_repository: PanelRepository,
        character_repository: CharacterRepository,
        character_appearance_repository: CharacterAppearanceRepository,
        mask_artifact_repository: MaskArtifactRepository,
    ) -> None:
        self._analysis_repository = analysis_repository
        self._panel_repository = panel_repository
        self._character_repository = character_repository
        self._character_appearance_repository = character_appearance_repository
        self._mask_artifact_repository = mask_artifact_repository

    async def execute(self, input_data: GetAnalysisInput) -> GetAnalysisOutput:
        """Execute the get analysis use case.

        Raises:
            NotFoundError: when no analysis matches the given analysis_id.
        """
        analysis = await self._analysis_repository.get(
            analysis_id=input_data.analysis_id
        )
        if analysis is None:
            raise NotFoundError(
                message="Analysis not found.",
                details={"field": "analysis_id", "reason": "not_found"},
            )

        panels_output: list[PanelOutput] = []
        panel_entities = await self._panel_repository.list(page_id=analysis.page_id)
        for panel_entity in panel_entities:
            panels_output.append(
                PanelOutput(
                    id=str(panel_entity.id),
                    page_id=str(panel_entity.page_id),
                    numero_orden=int(panel_entity.numero_orden),
                    x=float(panel_entity.x),
                    y=float(panel_entity.y),
                    ancho=float(panel_entity.ancho),
                    alto=float(panel_entity.alto),
                    confianza_deteccion=panel_entity.confianza_deteccion,
                )
            )

        appearances_output: list[CharacterAppearanceOutput] = []
        appearance_entities = await self._character_appearance_repository.list(
            page_id=analysis.page_id
        )
        characters_by_id: dict[UUID, CharacterOutput] = {}
        masks_by_appearance: dict[UUID, list[MaskArtifactOutput]] = {}

        for appearance_entity in appearance_entities:
            appearances_output.append(
                CharacterAppearanceOutput(
                    id=str(appearance_entity.id),
                    page_id=str(appearance_entity.page_id),
                    character_id=str(appearance_entity.character_id),
                    panel_id=(
                        str(appearance_entity.panel_id)
                        if appearance_entity.panel_id is not None
                        else None
                    ),
                    confianza_deteccion=appearance_entity.confianza_deteccion,
                )
            )

            character_id = appearance_entity.character_id
            if character_id not in characters_by_id:
                character_entity = await self._character_repository.get(
                    character_id=character_id
                )
                if character_entity is not None:
                    characters_by_id[character_id] = CharacterOutput(
                        id=str(character_entity.id),
                        nombre=str(character_entity.nombre),
                        descripcion=character_entity.descripcion,
                        confianza_identidad=character_entity.confianza_identidad,
                    )

            mask_entities = await self._mask_artifact_repository.list(
                appearance_id=appearance_entity.id
            )
            masks_by_appearance[appearance_entity.id] = [
                MaskArtifactOutput(
                    id=str(mask_entity.id),
                    appearance_id=str(mask_entity.appearance_id),
                    tipo_mascara=str(mask_entity.tipo_mascara),
                    ruta_archivo=str(mask_entity.ruta_archivo),
                    hash_sha256=str(mask_entity.hash_sha256),
                    ancho=mask_entity.ancho,
                    alto=mask_entity.alto,
                )
                for mask_entity in mask_entities
            ]

        characters_output = list(characters_by_id.values())
        masks_output: list[MaskArtifactOutput] = []
        for mask_list in masks_by_appearance.values():
            masks_output.extend(mask_list)

        return GetAnalysisOutput(
            analysis_id=str(analysis.id),
            page_id=str(analysis.page_id),
            estado=str(analysis.estado),
            confianza_global=analysis.confianza_global,
            version_modelo=analysis.version_modelo,
            panels=panels_output,
            characters=characters_output,
            appearances=appearances_output,
            masks=masks_output,
        )

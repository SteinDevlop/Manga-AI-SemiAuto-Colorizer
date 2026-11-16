"""Correct a mask artifact for a character appearance.

Marks an existing mask as corrected and records the region corrections.
Depends on injected repository and storage ports, never on concrete ORM
models. Stores only metadata and file paths -- no binary image content.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from app.core.exceptions import NotFoundError, ValidationError


class ArtifactRepository(Protocol):
    """Port for mask artifact persistence operations."""

    async def list_by_appearance(  # pragma: no cover - protocol stub
        self, *, appearance_id: UUID
    ) -> list[Any]:
        """Return mask artifacts for the given appearance id."""
        ...

    async def update(  # pragma: no cover - protocol stub
        self, *, artifact_id: UUID, **kwargs: Any
    ) -> Any | None:
        """Update a mask artifact by id, returning it or None when absent."""
        ...


@dataclass(frozen=True)
class CorrectMaskInput:
    """Input data for correcting a mask."""

    appearance_id: UUID
    correcciones: dict[str, Any]


@dataclass(frozen=True)
class CorrectMaskOutput:
    """Simple output DTO for a corrected mask, never an ORM model."""

    artifact_id: str
    appearance_id: str
    tipo_mascara: str
    ruta_archivo: str
    hash_sha256: str
    version: int
    corregido: bool
    correcciones: dict[str, Any]


class CorrectMaskUseCase:
    """Correct an existing mask for a character appearance.

    Marks the mask for ``appearance_id`` as corrected, records the region
    corrections, and increments its version. Raises NotFoundError when no
    mask exists for the appearance. Returns a DTO, never an ORM model.

    Raises:
        ValidationError: when ``correcciones`` is empty.
        NotFoundError: when no mask exists for the appearance.
    """

    def __init__(
        self,
        *,
        artifact_repository: ArtifactRepository,
    ) -> None:
        self._artifact_repository = artifact_repository

    async def execute(self, input_data: CorrectMaskInput) -> CorrectMaskOutput:
        """Execute the correct mask use case."""
        if not input_data.correcciones:
            raise ValidationError(
                message="correcciones must not be empty.",
                details={"field": "correcciones", "reason": "required"},
            )

        existing = await self._artifact_repository.list_by_appearance(
            appearance_id=input_data.appearance_id
        )
        if not existing:
            raise NotFoundError(
                message="No mask found for the given appearance.",
                details={
                    "field": "appearance_id",
                    "reason": "not_found",
                },
            )

        artifact = existing[0]

        updated = await self._artifact_repository.update(
            artifact_id=artifact.id,
            version=int(artifact.version) + 1,
            corregido=True,
            correcciones=input_data.correcciones,
        )
        if updated is None:
            raise NotFoundError(
                message="Mask artifact not found.",
                details={
                    "field": "appearance_id",
                    "reason": "not_found",
                },
            )

        return CorrectMaskOutput(
            artifact_id=str(updated.id),
            appearance_id=str(updated.appearance_id),
            tipo_mascara=str(updated.tipo_mascara),
            ruta_archivo=str(updated.ruta_archivo),
            hash_sha256=str(updated.hash_sha256),
            version=int(updated.version),
            corregido=True,
            correcciones=dict(input_data.correcciones),
        )

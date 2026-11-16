"""List artifacts use case.

Returns a list of artifacts with optional filters by type, page id, and job id.
Depends on the artifact repository port, never on concrete ORM models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.core.exceptions import ValidationError


class ArtifactRepository(Protocol):
    """Port for artifact persistence operations."""

    async def list(  # pragma: no cover - protocol stub
        self,
        *,
        artifact_type: str | None = None,
        page_id: str | None = None,
        job_id: str | None = None,
        skip: int = 0,
        limit: int | None = None,
    ) -> list[object]:
        """Return a page of artifacts, optionally filtered."""
        ...


@dataclass(frozen=True)
class ListArtifactsInput:
    """Input data for listing artifacts."""

    artifact_type: str | None = None
    page_id: str | None = None
    job_id: str | None = None
    skip: int = 0
    limit: int | None = None


@dataclass(frozen=True)
class ArtifactOutput:
    """Simple output DTO for an artifact, never an ORM model."""

    artifact_id: str
    tipo: str
    ruta_archivo: str
    hash_sha256: str
    tamano_bytes: int
    nombre_original: str | None
    mime_type: str | None
    ancho: int | None
    alto: int | None


@dataclass(frozen=True)
class ListArtifactsOutput:
    """List of artifacts with pagination metadata."""

    items: list[ArtifactOutput]
    skip: int
    limit: int | None


class ListArtifactsUseCase:
    """List artifacts with optional filters and pagination."""

    def __init__(
        self,
        artifact_repository: ArtifactRepository,
    ) -> None:
        self._artifact_repository = artifact_repository

    async def execute(self, input_data: ListArtifactsInput) -> ListArtifactsOutput:
        """Execute the list artifacts use case.

        Raises:
            ValidationError: when skip is negative or limit is non-positive.
        """
        if input_data.skip < 0:
            raise ValidationError(
                message="Skip must be non-negative.",
                details={"field": "skip", "reason": "invalid"},
            )
        if input_data.limit is not None and input_data.limit <= 0:
            raise ValidationError(
                message="Limit must be positive.",
                details={"field": "limit", "reason": "invalid"},
            )

        entities = await self._artifact_repository.list(
            artifact_type=input_data.artifact_type,
            page_id=input_data.page_id,
            job_id=input_data.job_id,
            skip=input_data.skip,
            limit=input_data.limit,
        )

        return ListArtifactsOutput(
            items=[
                ArtifactOutput(
                    artifact_id=str(entity.id),
                    tipo=entity.artifact_type,
                    ruta_archivo=entity.ruta_archivo,
                    hash_sha256=entity.hash_sha256,
                    tamano_bytes=entity.tamano_bytes,
                    nombre_original=entity.nombre_original,
                    mime_type=entity.mime_type,
                    ancho=entity.ancho,
                    alto=entity.alto,
                )
                for entity in entities
            ],
            skip=input_data.skip,
            limit=input_data.limit,
        )

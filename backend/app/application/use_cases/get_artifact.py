"""Get artifact use case.

Returns artifact data by artifact_id and artifact_type, validating existence
in both the storage service and the artifact repository.

Depends on repository and storage ports, never on concrete ORM models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.core.exceptions import NotFoundError


class ArtifactRepository(Protocol):
    """Port for artifact persistence operations."""

    async def get_by_id(self, *, artifact_id: str) -> object | None:  # pragma: no cover - protocol stub
        """Return the artifact with the given ID, or None when not found."""
        ...

    async def exists(self, *, artifact_id: str) -> bool:  # pragma: no cover - protocol stub
        """Return True when an artifact with the given ID exists."""
        ...


class StorageService(Protocol):
    """Port for artifact storage operations."""

    def exists(self, *, artifact_id: str, artifact_type: str) -> bool:  # pragma: no cover - protocol stub
        """Return True when the artifact exists in storage."""
        ...

    def read(self, *, artifact_id: str, artifact_type: str) -> bytes:  # pragma: no cover - protocol stub
        """Return the binary content of the artifact."""
        ...


@dataclass(frozen=True)
class GetArtifactInput:
    """Input data for getting an artifact."""

    artifact_id: str
    artifact_type: str


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
    contenido: bytes | None


class GetArtifactUseCase:
    """Retrieve an artifact by ID and type."""

    def __init__(
        self,
        artifact_repository: ArtifactRepository,
        storage_service: StorageService,
    ) -> None:
        self._artifact_repository = artifact_repository
        self._storage_service = storage_service

    async def execute(self, input_data: GetArtifactInput) -> ArtifactOutput:
        """Execute the get artifact use case.

        Raises:
            NotFoundError: when the artifact does not exist in storage or
                the repository.
        """
        if not self._storage_service.exists(
            artifact_id=input_data.artifact_id,
            artifact_type=input_data.artifact_type,
        ):
            raise NotFoundError(
                message="Artifact not found in storage.",
                details={
                    "field": "artifact_id",
                    "artifact_type": input_data.artifact_type,
                    "reason": "not_found",
                },
            )

        entity = await self._artifact_repository.get_by_id(
            artifact_id=input_data.artifact_id
        )
        if entity is None:
            raise NotFoundError(
                message="Artifact not found in repository.",
                details={
                    "field": "artifact_id",
                    "artifact_type": input_data.artifact_type,
                    "reason": "not_found",
                },
            )

        contenido = self._storage_service.read(
            artifact_id=input_data.artifact_id,
            artifact_type=input_data.artifact_type,
        )

        return ArtifactOutput(
            artifact_id=str(entity.id),
            tipo=input_data.artifact_type,
            ruta_archivo=entity.ruta_archivo,
            hash_sha256=entity.hash_sha256,
            tamano_bytes=entity.tamano_bytes,
            nombre_original=entity.nombre_original,
            mime_type=entity.mime_type,
            ancho=entity.ancho,
            alto=entity.alto,
            contenido=contenido,
        )

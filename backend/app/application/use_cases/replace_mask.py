"""Replace a mask artifact with a new version for a character appearance.

Replaces the existing mask for an appearance, incrementing its version.
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


class StorageService(Protocol):
    """Port for file storage operations."""

    def sha256_of_file(self, path: str) -> str:  # pragma: no cover - protocol stub
        """Return the SHA-256 hash of the file at ``path``."""
        ...


@dataclass(frozen=True)
class ReplaceMaskInput:
    """Input data for replacing a mask."""

    appearance_id: UUID
    nueva_ruta_archivo: str
    nuevo_hash_sha256: str


@dataclass(frozen=True)
class ReplaceMaskOutput:
    """Simple output DTO for a replaced mask, never an ORM model."""

    artifact_id: str
    appearance_id: str
    tipo_mascara: str
    ruta_archivo: str
    hash_sha256: str
    version: int


class ReplaceMaskUseCase:
    """Replace an existing mask with a new version.

    Locates the mask for ``appearance_id`` and replaces its file path, hash,
    and version (incremented by one). Raises NotFoundError when no mask
    exists for the appearance. Returns a DTO with the new version, never an
    ORM model.

    Raises:
        ValidationError: when the provided hash does not match the file at
            ``nueva_ruta_archivo``.
        NotFoundError: when no mask exists for the appearance.
    """

    def __init__(
        self,
        *,
        artifact_repository: ArtifactRepository,
        storage_service: StorageService,
    ) -> None:
        self._artifact_repository = artifact_repository
        self._storage_service = storage_service

    async def execute(self, input_data: ReplaceMaskInput) -> ReplaceMaskOutput:
        """Execute the replace mask use case."""
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

        computed_hash = self._storage_service.sha256_of_file(input_data.nueva_ruta_archivo)
        if computed_hash != input_data.nuevo_hash_sha256:
            raise ValidationError(
                message="Provided hash does not match the file content.",
                details={
                    "field": "nuevo_hash_sha256",
                    "reason": "hash_mismatch",
                    "expected": computed_hash,
                },
            )

        updated = await self._artifact_repository.update(
            artifact_id=artifact.id,
            ruta_archivo=input_data.nueva_ruta_archivo,
            hash_sha256=input_data.nuevo_hash_sha256,
            version=int(artifact.version) + 1,
        )
        if updated is None:
            raise NotFoundError(
                message="Mask artifact not found.",
                details={
                    "field": "appearance_id",
                    "reason": "not_found",
                },
            )

        return ReplaceMaskOutput(
            artifact_id=str(updated.id),
            appearance_id=str(updated.appearance_id),
            tipo_mascara=str(updated.tipo_mascara),
            ruta_archivo=str(updated.ruta_archivo),
            hash_sha256=str(updated.hash_sha256),
            version=int(updated.version),
        )

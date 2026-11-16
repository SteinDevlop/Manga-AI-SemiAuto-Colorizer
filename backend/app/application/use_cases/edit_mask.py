"""Edit or create a mask artifact for a character appearance.

Updates an existing mask or creates a new one for an appearance.
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

    async def create(  # pragma: no cover - protocol stub
        self, **kwargs: Any
    ) -> Any:
        """Create and persist a mask artifact, returning the persisted entity."""
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
class EditMaskInput:
    """Input data for editing or creating a mask."""

    appearance_id: UUID
    tipo_mascara: str
    ruta_archivo: str | None = None
    hash_sha256: str | None = None


@dataclass(frozen=True)
class MaskOutput:
    """Simple output DTO for a mask artifact, never an ORM model."""

    artifact_id: str
    appearance_id: str
    tipo_mascara: str
    ruta_archivo: str
    hash_sha256: str
    version: int


class EditMaskUseCase:
    """Edit or create a mask artifact for a character appearance.

    When a mask already exists for ``appearance_id`` it is updated with the
    provided fields. When none exists, a new mask is created; in that case
    ``ruta_archivo`` and ``hash_sha256`` are required. Returns a DTO with the
    artifact id and metadata, never an ORM model.

    Raises:
        ValidationError: when creating a new mask without a file path/hash,
            or when ``tipo_mascara`` is empty.
        NotFoundError: when updating a non-existent mask.
    """

    def __init__(
        self,
        *,
        artifact_repository: ArtifactRepository,
        storage_service: StorageService,
    ) -> None:
        self._artifact_repository = artifact_repository
        self._storage_service = storage_service

    async def execute(self, input_data: EditMaskInput) -> MaskOutput:
        """Execute the edit/create mask use case."""
        if not input_data.tipo_mascara or not input_data.tipo_mascara.strip():
            raise ValidationError(
                message="tipo_mascara is required.",
                details={"field": "tipo_mascara", "reason": "required"},
            )

        existing = await self._artifact_repository.list_by_appearance(
            appearance_id=input_data.appearance_id
        )

        hash_sha256 = input_data.hash_sha256
        ruta_archivo = input_data.ruta_archivo

        if ruta_archivo is not None and hash_sha256 is None:
            hash_sha256 = self._storage_service.sha256_of_file(ruta_archivo)

        if existing:
            artifact = existing[0]
            updates: dict[str, Any] = {"tipo_mascara": input_data.tipo_mascara}
            if ruta_archivo is not None:
                updates["ruta_archivo"] = ruta_archivo
            if hash_sha256 is not None:
                updates["hash_sha256"] = hash_sha256
            updated = await self._artifact_repository.update(artifact_id=artifact.id, **updates)
            if updated is None:
                raise NotFoundError(
                    message="Mask artifact not found.",
                    details={
                        "field": "appearance_id",
                        "reason": "not_found",
                    },
                )
            return MaskOutput(
                artifact_id=str(updated.id),
                appearance_id=str(updated.appearance_id),
                tipo_mascara=str(updated.tipo_mascara),
                ruta_archivo=str(updated.ruta_archivo),
                hash_sha256=str(updated.hash_sha256),
                version=int(updated.version),
            )

        if ruta_archivo is None or hash_sha256 is None:
            raise ValidationError(
                message="ruta_archivo and hash_sha256 are required to create a new mask.",
                details={
                    "field": "ruta_archivo",
                    "reason": "required_on_create",
                },
            )

        created = await self._artifact_repository.create(
            appearance_id=input_data.appearance_id,
            tipo_mascara=input_data.tipo_mascara,
            ruta_archivo=ruta_archivo,
            hash_sha256=hash_sha256,
        )

        return MaskOutput(
            artifact_id=str(created.id),
            appearance_id=str(created.appearance_id),
            tipo_mascara=str(created.tipo_mascara),
            ruta_archivo=str(created.ruta_archivo),
            hash_sha256=str(created.hash_sha256),
            version=int(created.version),
        )

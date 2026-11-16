"""Upload file use case.

Validates an uploaded file (MIME type, size, content, dimensions), stores it
through the storage service, persists metadata in the artifact repository, and
returns a DTO with the artifact id and metadata.

Depends on repository and validator ports, never on concrete ORM models or AI
implementations.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from app.core.exceptions import ConflictError, ValidationError


class ArtifactRepository(Protocol):
    """Port for artifact persistence operations."""

    async def exists_by_hash(self, *, hash_sha256: str) -> bool:  # pragma: no cover - protocol stub
        """Return True when an artifact with the given hash already exists."""
        ...

    async def create(  # pragma: no cover - protocol stub
        self,
        *,
        artifact_type: str,
        hash_sha256: str,
        ruta_archivo: str,
        nombre_original: str | None,
        mime_type: str | None,
        tamano_bytes: int,
        ancho: int | None,
        alto: int | None,
    ) -> object:
        """Create and persist an artifact record, returning the persisted entity."""
        ...


class FileValidator(Protocol):
    """Port for file validation operations."""

    async def validate_mime_type(  # pragma: no cover - protocol stub
        self,
        *,
        path: str | Path,
        artifact_type: str,
    ) -> None:
        """Validate the MIME type of the file at ``path``.

        Raises:
            ValidationError: when the MIME type is not allowed.
        """
        ...

    async def validate_size(  # pragma: no cover - protocol stub
        self,
        *,
        path: str | Path,
        artifact_type: str,
    ) -> None:
        """Validate the size of the file at ``path``.

        Raises:
            ValidationError: when the size exceeds the limit.
        """
        ...

    async def validate_content(  # pragma: no cover - protocol stub
        self,
        *,
        path: str | Path,
    ) -> None:
        """Validate the real content of the file at ``path`` against its extension.

        Raises:
            ValidationError: when the content does not match the extension.
        """
        ...

    async def validate_dimensions(  # pragma: no cover - protocol stub
        self,
        *,
        path: str | Path,
        artifact_type: str,
    ) -> None:
        """Validate the dimensions of the image file at ``path``.

        Raises:
            ValidationError: when dimensions exceed the limits.
        """
        ...


@dataclass(frozen=True)
class UploadFileInput:
    """Input data for uploading a file."""

    source_path: str | Path
    artifact_type: str
    original_name: str | None = None


@dataclass(frozen=True)
class ArtifactOutput:
    """Simple output DTO for an uploaded artifact, never an ORM model."""

    artifact_id: str
    tipo: str
    ruta_archivo: str
    hash_sha256: str
    tamano_bytes: int
    nombre_original: str | None
    mime_type: str | None
    ancho: int | None
    alto: int | None


class UploadFileUseCase:
    """Upload, validate, store, and register a file artifact."""

    def __init__(
        self,
        artifact_repository: ArtifactRepository,
        storage_service: Any,
        file_validator: FileValidator,
    ) -> None:
        self._artifact_repository = artifact_repository
        self._storage_service = storage_service
        self._file_validator = file_validator

    async def execute(self, input_data: UploadFileInput) -> ArtifactOutput:
        """Execute the upload file use case.

        Raises:
            ValidationError: when any validation rule fails.
            ConflictError: when the file hash is already registered.
        """
        path = Path(input_data.source_path)

        await self._file_validator.validate_mime_type(
            path=path, artifact_type=input_data.artifact_type
        )
        await self._file_validator.validate_size(
            path=path, artifact_type=input_data.artifact_type
        )
        await self._file_validator.validate_content(path=path)
        await self._file_validator.validate_dimensions(
            path=path, artifact_type=input_data.artifact_type
        )

        saved = self._storage_service.save(
            source_path=path,
            artifact_type=input_data.artifact_type,
            original_name=input_data.original_name,
        )

        hash_sha256 = saved["hash_sha256"]
        if await self._artifact_repository.exists_by_hash(hash_sha256=hash_sha256):
            raise ConflictError(
                message="An artifact with this hash already exists.",
                details={"field": "hash_sha256", "reason": "duplicate_hash"},
            )

        entity = await self._artifact_repository.create(
            artifact_type=input_data.artifact_type,
            hash_sha256=hash_sha256,
            ruta_archivo=saved["ruta_archivo"],
            nombre_original=saved["nombre_original"],
            mime_type=None,
            tamano_bytes=saved["tamano_bytes"],
            ancho=None,
            alto=None,
        )

        return ArtifactOutput(
            artifact_id=str(entity.id),
            tipo=input_data.artifact_type,
            ruta_archivo=saved["ruta_archivo"],
            hash_sha256=hash_sha256,
            tamano_bytes=saved["tamano_bytes"],
            nombre_original=saved["nombre_original"],
            mime_type=None,
            ancho=None,
            alto=None,
        )

"""Delete artifact use case.

Deletes an artifact from storage and from the repository, returning a bool.
Raises NotFoundError when the artifact does not exist.

Depends on repository and storage ports, never on concrete ORM models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.core.exceptions import NotFoundError


class ArtifactRepository(Protocol):
    """Port for artifact persistence operations."""

    async def exists(self, *, artifact_id: str) -> bool:  # pragma: no cover - protocol stub
        """Return True when an artifact with the given ID exists."""
        ...

    async def delete(self, *, artifact_id: str) -> bool:  # pragma: no cover - protocol stub
        """Delete the artifact with the given ID. Returns False if absent."""
        ...


class StorageService(Protocol):
    """Port for artifact storage operations."""

    def exists(
        self, *, artifact_id: str, artifact_type: str
    ) -> bool:  # pragma: no cover - protocol stub
        """Return True when the artifact exists in storage."""
        ...

    def delete(
        self, *, artifact_id: str, artifact_type: str
    ) -> bool:  # pragma: no cover - protocol stub
        """Delete the artifact from storage. Returns False if absent."""
        ...


@dataclass(frozen=True)
class DeleteArtifactInput:
    """Input data for deleting an artifact."""

    artifact_id: str
    artifact_type: str


@dataclass(frozen=True)
class DeleteArtifactOutput:
    """Output DTO for artifact deletion."""

    deleted: bool


class DeleteArtifactUseCase:
    """Delete an artifact from storage and the repository."""

    def __init__(
        self,
        artifact_repository: ArtifactRepository,
        storage_service: StorageService,
    ) -> None:
        self._artifact_repository = artifact_repository
        self._storage_service = storage_service

    async def execute(self, input_data: DeleteArtifactInput) -> DeleteArtifactOutput:
        """Execute the delete artifact use case.

        Raises:
            NotFoundError: when the artifact does not exist in storage or
                the repository.
        """
        if not await self._artifact_repository.exists(artifact_id=input_data.artifact_id):
            raise NotFoundError(
                message="Artifact not found in repository.",
                details={
                    "field": "artifact_id",
                    "artifact_type": input_data.artifact_type,
                    "reason": "not_found",
                },
            )

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

        storage_deleted = self._storage_service.delete(
            artifact_id=input_data.artifact_id,
            artifact_type=input_data.artifact_type,
        )
        repository_deleted = await self._artifact_repository.delete(
            artifact_id=input_data.artifact_id
        )

        return DeleteArtifactOutput(deleted=storage_deleted and repository_deleted)

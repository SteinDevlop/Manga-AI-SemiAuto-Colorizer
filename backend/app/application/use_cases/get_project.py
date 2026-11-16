"""Get project use case.

Returns a project by its ID or raises NotFoundError when missing.
Depends on the project repository port, never on concrete ORM models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.core.exceptions import NotFoundError


class ProjectRepository(Protocol):
    """Port for project persistence operations."""

    async def get_by_id(
        self, *, project_id: UUID
    ) -> object | None:  # pragma: no cover - protocol stub
        """Return the project with the given ID, or None when not found."""
        ...


@dataclass(frozen=True)
class GetProjectInput:
    """Input data for getting a project."""

    project_id: UUID


@dataclass(frozen=True)
class ProjectOutput:
    """Simple output DTO for a project, never an ORM model."""

    id: str
    nombre: str
    descripcion: str | None
    created_at: str


class GetProjectUseCase:
    """Retrieve a project by ID."""

    def __init__(
        self,
        project_repository: ProjectRepository,
    ) -> None:
        self._project_repository = project_repository

    async def execute(self, input_data: GetProjectInput) -> ProjectOutput:
        """Execute the get project use case.

        Raises:
            NotFoundError: when no project matches the given ID.
        """
        entity = await self._project_repository.get_by_id(project_id=input_data.project_id)
        if entity is None:
            raise NotFoundError(
                message="Project not found.",
                details={"field": "project_id", "reason": "not_found"},
            )

        return ProjectOutput(
            id=str(entity.id),
            nombre=entity.nombre,
            descripcion=entity.descripcion,
            created_at=entity.created_at.isoformat(),
        )

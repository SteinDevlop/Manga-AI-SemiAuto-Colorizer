"""Create project use case.

Creates a new project with a unique name and optional description.
Depends on the project repository port, never on concrete ORM models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.core.exceptions import ConflictError


class ProjectRepository(Protocol):
    """Port for project persistence operations."""

    async def exists_by_name(self, *, name: str) -> bool:  # pragma: no cover - protocol stub
        """Return True when a project with the given name already exists."""
        ...

    async def create(
        self, *, name: str, description: str | None
    ) -> object:  # pragma: no cover - protocol stub
        """Create and persist a project, returning the persisted entity."""
        ...


@dataclass(frozen=True)
class CreateProjectInput:
    """Input data for creating a project."""

    nombre: str
    descripcion: str | None = None


@dataclass(frozen=True)
class ProjectOutput:
    """Simple output DTO for a project, never an ORM model."""

    id: str
    nombre: str
    descripcion: str | None
    created_at: str


class CreateProjectUseCase:
    """Create a project ensuring its name is unique."""

    def __init__(
        self,
        project_repository: ProjectRepository,
    ) -> None:
        self._project_repository = project_repository

    async def execute(self, input_data: CreateProjectInput) -> ProjectOutput:
        """Execute the create project use case.

        Raises:
            ConflictError: when a project with the same name already exists.
        """
        if await self._project_repository.exists_by_name(name=input_data.nombre):
            raise ConflictError(
                message="A project with this name already exists.",
                details={"field": "nombre", "reason": "duplicate_name"},
            )

        entity = await self._project_repository.create(
            name=input_data.nombre,
            description=input_data.descripcion,
        )

        return ProjectOutput(
            id=str(entity.id),
            nombre=entity.nombre,
            descripcion=entity.descripcion,
            created_at=entity.created_at.isoformat(),
        )

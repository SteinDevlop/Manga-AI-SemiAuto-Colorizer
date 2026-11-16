"""List projects use case.

Returns a paginated list of projects with optional skip/limit.
Depends on the project repository port, never on concrete ORM models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.core.exceptions import ValidationError


class ProjectRepository(Protocol):
    """Port for project persistence operations."""

    async def list(  # pragma: no cover - protocol stub
        self,
        *,
        skip: int = 0,
        limit: int | None = None,
    ) -> list[object]:
        """Return a page of projects."""
        ...


@dataclass(frozen=True)
class ListProjectsInput:
    """Input data for listing projects."""

    skip: int = 0
    limit: int | None = None


@dataclass(frozen=True)
class ProjectOutput:
    """Simple output DTO for a project, never an ORM model."""

    id: str
    nombre: str
    descripcion: str | None
    created_at: str


@dataclass(frozen=True)
class ListProjectsOutput:
    """Paginated list of projects."""

    items: list[ProjectOutput]
    skip: int
    limit: int | None


class ListProjectsUseCase:
    """List projects with optional pagination."""

    def __init__(
        self,
        project_repository: ProjectRepository,
    ) -> None:
        self._project_repository = project_repository

    async def execute(self, input_data: ListProjectsInput) -> ListProjectsOutput:
        """Execute the list projects use case.

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

        entities = await self._project_repository.list(
            skip=input_data.skip,
            limit=input_data.limit,
        )

        return ListProjectsOutput(
            items=[
                ProjectOutput(
                    id=str(entity.id),
                    nombre=entity.nombre,
                    descripcion=entity.descripcion,
                    created_at=entity.created_at.isoformat(),
                )
                for entity in entities
            ],
            skip=input_data.skip,
            limit=input_data.limit,
        )

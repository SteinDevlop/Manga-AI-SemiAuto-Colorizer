"""List pages use case.

Returns the pages of a given project with optional pagination.
Depends on the page repository port, never on concrete ORM models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.core.exceptions import NotFoundError, ValidationError


class PageRepository(Protocol):
    """Port for page persistence operations."""

    async def exists_project(self, *, project_id: UUID) -> bool:  # pragma: no cover - protocol stub
        """Return True when the referenced project exists."""
        ...

    async def list_by_project(  # pragma: no cover - protocol stub
        self,
        *,
        project_id: UUID,
        skip: int = 0,
        limit: int | None = None,
    ) -> list[object]:
        """Return pages of the given project."""
        ...


@dataclass(frozen=True)
class ListPagesInput:
    """Input data for listing pages of a project."""

    project_id: UUID
    skip: int = 0
    limit: int | None = None


@dataclass(frozen=True)
class PageOutput:
    """Simple output DTO for a page, never an ORM model."""

    id: str
    project_id: str
    nombre_archivo_original: str
    hash_sha256: str
    ruta_archivo: str
    mime_type: str | None
    ancho: int | None
    alto: int | None
    tamano_bytes: int | None
    estado: str
    created_at: str


@dataclass(frozen=True)
class ListPagesOutput:
    """Paginated list of pages for a project."""

    items: list[PageOutput]
    skip: int
    limit: int | None


class ListPagesUseCase:
    """List pages of a project with optional pagination."""

    def __init__(
        self,
        page_repository: PageRepository,
    ) -> None:
        self._page_repository = page_repository

    async def execute(self, input_data: ListPagesInput) -> ListPagesOutput:
        """Execute the list pages use case.

        Raises:
            ValidationError: when skip is negative or limit is non-positive.
            NotFoundError: when the referenced project does not exist.
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

        if not await self._page_repository.exists_project(project_id=input_data.project_id):
            raise NotFoundError(
                message="Referenced project not found.",
                details={"field": "project_id", "reason": "not_found"},
            )

        entities = await self._page_repository.list_by_project(
            project_id=input_data.project_id,
            skip=input_data.skip,
            limit=input_data.limit,
        )

        return ListPagesOutput(
            items=[
                PageOutput(
                    id=str(entity.id),
                    project_id=str(entity.project_id),
                    nombre_archivo_original=entity.nombre_archivo_original,
                    hash_sha256=entity.hash_sha256,
                    ruta_archivo=entity.ruta_archivo,
                    mime_type=entity.mime_type,
                    ancho=entity.ancho,
                    alto=entity.alto,
                    tamano_bytes=entity.tamano_bytes,
                    estado=entity.estado,
                    created_at=entity.created_at.isoformat(),
                )
                for entity in entities
            ],
            skip=input_data.skip,
            limit=input_data.limit,
        )

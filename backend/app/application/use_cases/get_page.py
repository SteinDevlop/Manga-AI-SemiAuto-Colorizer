"""Get page use case.

Returns a page by its ID or raises NotFoundError when missing.
Depends on the page repository port, never on concrete ORM models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.core.exceptions import NotFoundError


class PageRepository(Protocol):
    """Port for page persistence operations."""

    async def get_by_id(self, *, page_id: UUID) -> object | None:  # pragma: no cover - protocol stub
        """Return the page with the given ID, or None when not found."""
        ...


@dataclass(frozen=True)
class GetPageInput:
    """Input data for getting a page."""

    page_id: UUID


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


class GetPageUseCase:
    """Retrieve a page by ID."""

    def __init__(
        self,
        page_repository: PageRepository,
    ) -> None:
        self._page_repository = page_repository

    async def execute(self, input_data: GetPageInput) -> PageOutput:
        """Execute the get page use case.

        Raises:
            NotFoundError: when no page matches the given ID.
        """
        entity = await self._page_repository.get_by_id(page_id=input_data.page_id)
        if entity is None:
            raise NotFoundError(
                message="Page not found.",
                details={"field": "page_id", "reason": "not_found"},
            )

        return PageOutput(
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

"""Create page use case.

Creates a page after validating the referenced project exists and the
page hash is not duplicated. Depends on repository ports, never on
concrete ORM models.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.core.exceptions import ConflictError, NotFoundError
from app.core.logging import get_logger

logger = get_logger(__name__)


class ProjectRepository(Protocol):
    """Port for project persistence operations."""

    async def exists(self, *, project_id: UUID) -> bool:  # pragma: no cover - protocol stub
        """Return True when a project with the given ID exists."""
        ...


class PageRepository(Protocol):
    """Port for page persistence operations."""

    async def exists_by_hash(self, *, hash_sha256: str) -> bool:  # pragma: no cover - protocol stub
        """Return True when a page with the given hash already exists."""
        ...

    async def create(  # pragma: no cover - protocol stub
        self,
        *,
        project_id: UUID,
        nombre_archivo_original: str,
        hash_sha256: str,
        ruta_archivo: str,
        mime_type: str | None,
        ancho: int | None,
        alto: int | None,
        tamano_bytes: int | None,
    ) -> object:
        """Create and persist a page, returning the persisted entity."""
        ...


@dataclass(frozen=True)
class CreatePageInput:
    """Input data for creating a page."""

    project_id: UUID
    nombre_archivo_original: str
    hash_sha256: str
    ruta_archivo: str
    mime_type: str | None = None
    ancho: int | None = None
    alto: int | None = None
    tamano_bytes: int | None = None
    allow_duplicate_hash: bool = False


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


class CreatePageUseCase:
    """Create a page after project existence and hash uniqueness checks."""

    def __init__(
        self,
        project_repository: ProjectRepository,
        page_repository: PageRepository,
    ) -> None:
        self._project_repository = project_repository
        self._page_repository = page_repository

    async def execute(self, input_data: CreatePageInput) -> PageOutput:
        """Execute the create page use case.

        Raises:
            NotFoundError: when the referenced project does not exist.
            ConflictError: when the hash_sha256 is already in use.
        """
        try:
            if not await self._project_repository.exists(project_id=input_data.project_id):
                logger.warning(
                    "Proyecto no encontrado para la página: %s", input_data.project_id
                )
                raise NotFoundError(
                    message="Referenced project not found.",
                    details={"field": "project_id", "reason": "not_found"},
                )

            if not input_data.allow_duplicate_hash and await self._page_repository.exists_by_hash(hash_sha256=input_data.hash_sha256):
                logger.warning(
                    "Hash de página duplicado: %s", input_data.hash_sha256
                )
                raise ConflictError(
                    message="A page with this hash already exists.",
                    details={"field": "hash_sha256", "reason": "duplicate_hash"},
                )

            entity = await self._page_repository.create(
                project_id=input_data.project_id,
                nombre_archivo_original=input_data.nombre_archivo_original,
                hash_sha256=input_data.hash_sha256,
                ruta_archivo=input_data.ruta_archivo,
                mime_type=input_data.mime_type,
                ancho=input_data.ancho,
                alto=input_data.alto,
                tamano_bytes=input_data.tamano_bytes,
            )

            logger.info(
                "Página creada exitosamente: %s (proyecto: %s)",
                entity.id,
                input_data.project_id,
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
        except ConflictError:
            raise
        except NotFoundError:
            raise
        except Exception as exc:  # pragma: no cover - infra failure path
            logger.exception(
                "Error al crear página para proyecto %s: %s",
                input_data.project_id,
                exc,
            )
            raise

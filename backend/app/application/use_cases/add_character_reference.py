"""Add character reference use case.

Adds or updates the stable reference of a character (a path or identifier)
used to reproduce color consistency across pages. If a memory already
exists for the character, its reference is updated; otherwise a new memory
is created with the given reference. Depends on repository ports only,
never on ORM models or AI model implementations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from app.core.exceptions import NotFoundError, ValidationError


class CharacterMemoryRepository(Protocol):
    """Port for character memory read/write operations."""

    async def get_by_character(  # pragma: no cover - protocol stub
        self, *, character_id: UUID
    ) -> Any | None:
        """Return the memory for the given character, or None when not found."""
        ...

    async def create(  # pragma: no cover - protocol stub
        self, **kwargs: Any
    ) -> Any:
        """Create and persist a new memory from the given attributes."""
        ...

    async def update(  # pragma: no cover - protocol stub
        self, *, memory_id: UUID, **kwargs: Any
    ) -> Any | None:
        """Update the attributes of the memory with the given id."""
        ...


@dataclass(frozen=True)
class AddCharacterReferenceInput:
    """Input data for adding a character reference."""

    character_id: UUID
    referencia_estable: str


@dataclass(frozen=True)
class CharacterMemoryOutput:
    """Simple output DTO for a character memory, never an ORM model."""

    character_id: str
    embedding: str | None
    embedding_model: str | None
    atributos_estables: dict[str, Any] | None
    atributos_escena: dict[str, Any] | None
    referencia_estable: str | None
    pagina_origen_id: str | None
    created_at: str | None
    updated_at: str | None


class AddCharacterReferenceUseCase:
    """Add or update the stable reference of a character.

    The stable reference enables color consistency across pages for the same
    character identity. The reference is a path or identifier, never binary
    image content.
    """

    def __init__(
        self,
        character_memory_repository: CharacterMemoryRepository,
    ) -> None:
        self._character_memory_repository = character_memory_repository

    async def execute(self, input_data: AddCharacterReferenceInput) -> CharacterMemoryOutput:
        """Execute the add character reference use case.

        Raises:
            ValidationError: when the reference is empty.
            NotFoundError: when the referenced character cannot be located.
        """
        if not input_data.referencia_estable or not input_data.referencia_estable.strip():
            raise ValidationError(
                message="The stable reference must not be empty.",
                details={"field": "referencia_estable", "reason": "empty"},
            )

        entity = await self._character_memory_repository.get_by_character(
            character_id=input_data.character_id
        )

        if entity is not None:
            updated = await self._character_memory_repository.update(
                memory_id=entity.id,
                referencia_estable=input_data.referencia_estable.strip(),
            )
            if updated is None:
                raise NotFoundError(
                    message="Character memory not found.",
                    details={"field": "character_id", "reason": "not_found"},
                )
            target = updated
        else:
            target = await self._character_memory_repository.create(
                character_id=input_data.character_id,
                referencia_estable=input_data.referencia_estable.strip(),
            )

        return CharacterMemoryOutput(
            character_id=str(target.character_id),
            embedding=target.embedding,
            embedding_model=target.embedding_model,
            atributos_estables=target.atributos_estables,
            atributos_escena=target.atributos_escena,
            referencia_estable=target.referencia_estable,
            pagina_origen_id=(str(target.pagina_origen_id) if target.pagina_origen_id else None),
            created_at=target.created_at.isoformat() if target.created_at else None,
            updated_at=target.updated_at.isoformat() if target.updated_at else None,
        )

"""Get character memory use case.

Returns the stable memory of a character (embedding, stable attributes,
scene attributes, stable reference) or raises NotFoundError when missing.
Depends on the character memory repository port, never on ORM models or AI
model implementations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from app.core.exceptions import NotFoundError


class CharacterMemoryRepository(Protocol):
    """Port for character memory read operations."""

    async def get_by_character(  # pragma: no cover - protocol stub
        self, *, character_id: UUID
    ) -> Any | None:
        """Return the memory for the given character, or None when not found."""
        ...

    async def update(  # pragma: no cover - protocol stub
        self, *, memory_id: UUID, **kwargs: Any
    ) -> Any | None:
        """Update the attributes of the memory with the given id."""
        ...


@dataclass(frozen=True)
class GetCharacterMemoryInput:
    """Input data for getting a character memory."""

    character_id: UUID


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


class GetCharacterMemoryUseCase:
    """Retrieve the stable memory of a character by its ID.

    Distinguishes stable attributes (hair, eyes) from scene attributes
    (wardrobe, accessories): a character may change clothes without
    changing identity.
    """

    def __init__(
        self,
        character_memory_repository: CharacterMemoryRepository,
    ) -> None:
        self._character_memory_repository = character_memory_repository

    async def execute(self, input_data: GetCharacterMemoryInput) -> CharacterMemoryOutput:
        """Execute the get character memory use case.

        Raises:
            NotFoundError: when no memory matches the given character ID.
        """
        entity = await self._character_memory_repository.get_by_character(
            character_id=input_data.character_id
        )
        if entity is None:
            raise NotFoundError(
                message="Character memory not found.",
                details={"field": "character_id", "reason": "not_found"},
            )

        return CharacterMemoryOutput(
            character_id=str(entity.character_id),
            embedding=entity.embedding,
            embedding_model=entity.embedding_model,
            atributos_estables=entity.atributos_estables,
            atributos_escena=entity.atributos_escena,
            referencia_estable=entity.referencia_estable,
            pagina_origen_id=(str(entity.pagina_origen_id) if entity.pagina_origen_id else None),
            created_at=entity.created_at.isoformat() if entity.created_at else None,
            updated_at=entity.updated_at.isoformat() if entity.updated_at else None,
        )

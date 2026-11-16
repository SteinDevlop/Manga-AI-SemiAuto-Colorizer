"""Update character memory use case.

Updates the stable memory of a character: stable attributes (hair, eyes),
scene attributes (wardrobe, accessories) and/or the stable reference.
A character may change clothes without changing identity. At least one
updatable field must be provided, otherwise ValidationError is raised.
Depends on repository ports only, never on ORM models or AI models.
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

    async def update(  # pragma: no cover - protocol stub
        self, *, memory_id: UUID, **kwargs: Any
    ) -> Any | None:
        """Update the attributes of the memory with the given id."""
        ...


@dataclass(frozen=True)
class UpdateCharacterMemoryInput:
    """Input data for updating a character memory.

    All attribute fields are optional; at least one must be provided.
    """

    character_id: UUID
    atributos_estables: dict[str, Any] | None = None
    atributos_escena: dict[str, Any] | None = None
    referencia_estable: str | None = None


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


class UpdateCharacterMemoryUseCase:
    """Update the stable memory of a character.

    Stable attributes (hair, eyes) describe the character's identity and
    persist across scenes. Scene attributes (wardrobe, accessories) describe
    the current appearance and may change without altering identity.
    """

    def __init__(
        self,
        character_memory_repository: CharacterMemoryRepository,
    ) -> None:
        self._character_memory_repository = character_memory_repository

    async def execute(self, input_data: UpdateCharacterMemoryInput) -> CharacterMemoryOutput:
        """Execute the update character memory use case.

        Raises:
            NotFoundError: when no memory matches the given character ID.
            ValidationError: when no updatable field is provided.
        """
        updates: dict[str, Any] = {}
        if input_data.atributos_estables is not None:
            updates["atributos_estables"] = input_data.atributos_estables
        if input_data.atributos_escena is not None:
            updates["atributos_escena"] = input_data.atributos_escena
        if input_data.referencia_estable is not None:
            updates["referencia_estable"] = input_data.referencia_estable

        if not updates:
            raise ValidationError(
                message="At least one field must be provided to update.",
                details={
                    "field": "atributos_estables,atributos_escena,referencia_estable",
                    "reason": "no_updatable_field",
                },
            )

        entity = await self._character_memory_repository.get_by_character(
            character_id=input_data.character_id
        )
        if entity is None:
            raise NotFoundError(
                message="Character memory not found.",
                details={"field": "character_id", "reason": "not_found"},
            )

        updated = await self._character_memory_repository.update(
            memory_id=entity.id,
            **updates,
        )
        if updated is None:
            raise NotFoundError(
                message="Character memory not found.",
                details={"field": "character_id", "reason": "not_found"},
            )

        return CharacterMemoryOutput(
            character_id=str(updated.character_id),
            embedding=updated.embedding,
            embedding_model=updated.embedding_model,
            atributos_estables=updated.atributos_estables,
            atributos_escena=updated.atributos_escena,
            referencia_estable=updated.referencia_estable,
            pagina_origen_id=(str(updated.pagina_origen_id) if updated.pagina_origen_id else None),
            created_at=updated.created_at.isoformat() if updated.created_at else None,
            updated_at=updated.updated_at.isoformat() if updated.updated_at else None,
        )

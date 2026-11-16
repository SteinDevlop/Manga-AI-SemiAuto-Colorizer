"""Edit character attribute use case.

Updates or creates a character attribute (e.g. hair, eyes, skin). Suggested
values are editable suggestions that mark uncertainty; they are never official
colors. Depends on injected repository protocol ports, never on concrete ORM
models or AI model implementations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from app.core.exceptions import NotFoundError, ValidationError


class CharacterAttributeRepository(Protocol):
    """Port for character attribute read/write operations."""

    async def get_by_character_and_name(  # pragma: no cover - protocol stub
        self, *, character_id: UUID, nombre_atributo: str
    ) -> Any | None:
        """Return the attribute for the character and name, or None."""
        ...

    async def create(  # pragma: no cover - protocol stub
        self, **kwargs: Any
    ) -> Any:
        """Create and persist a new attribute from the given attributes."""
        ...

    async def update(  # pragma: no cover - protocol stub
        self, *, attribute_id: UUID, **kwargs: Any
    ) -> Any | None:
        """Update the attributes of the attribute with the given id."""
        ...


@dataclass(frozen=True)
class EditCharacterAttributeInput:
    """Input data for editing a character attribute.

    ``valor_sugerido`` and ``confianza_sugerencia`` are optional editable
    suggestions that mark uncertainty; they are never official colors.
    """

    character_id: UUID
    nombre_atributo: str
    valor_sugerido: str | None = None
    confianza_sugerencia: float | None = None


@dataclass(frozen=True)
class CharacterAttributeOutput:
    """Simple output DTO for a character attribute, never an ORM model."""

    id: str
    character_id: str
    nombre_atributo: str
    valor_sugerido: str | None
    valor_aprobado: str | None
    esta_aprobado: bool
    confianza_sugerencia: float | None


class EditCharacterAttributeUseCase:
    """Update or create a character attribute.

    Suggested values are editable suggestions marking uncertainty; they never
    constitute official colors. The attribute is created when it does not
    exist yet, otherwise it is updated in place.
    """

    def __init__(
        self,
        *,
        character_attribute_repository: CharacterAttributeRepository,
    ) -> None:
        self._character_attribute_repository = character_attribute_repository

    async def execute(self, input_data: EditCharacterAttributeInput) -> CharacterAttributeOutput:
        """Execute the edit character attribute use case.

        Raises:
            NotFoundError: when the character cannot be located.
            ValidationError: when required input is missing or invalid.
        """
        if not input_data.nombre_atributo or not input_data.nombre_atributo.strip():
            raise ValidationError(
                message="nombre_atributo is required.",
                details={
                    "field": "nombre_atributo",
                    "reason": "required",
                },
            )

        nombre_atributo = input_data.nombre_atributo.strip()

        entity = await self._character_attribute_repository.get_by_character_and_name(
            character_id=input_data.character_id,
            nombre_atributo=nombre_atributo,
        )

        if entity is not None:
            updates: dict[str, Any] = {"nombre_atributo": nombre_atributo}
            if input_data.valor_sugerido is not None:
                updates["valor_sugerido"] = input_data.valor_sugerido
            if input_data.confianza_sugerencia is not None:
                updates["confianza_sugerencia"] = input_data.confianza_sugerencia

            updated = await self._character_attribute_repository.update(
                attribute_id=entity.id,
                **updates,
            )
            if updated is None:
                raise NotFoundError(
                    message="Character attribute not found.",
                    details={
                        "field": "character_id",
                        "reason": "not_found",
                    },
                )
            target = updated
        else:
            target = await self._character_attribute_repository.create(
                character_id=input_data.character_id,
                nombre_atributo=nombre_atributo,
                valor_sugerido=input_data.valor_sugerido,
                valor_aprobado=None,
                esta_aprobado=False,
                confianza_sugerencia=input_data.confianza_sugerencia,
            )

        return CharacterAttributeOutput(
            id=str(target.id),
            character_id=str(target.character_id),
            nombre_atributo=target.nombre_atributo,
            valor_sugerido=target.valor_sugerido,
            valor_aprobado=target.valor_aprobado,
            esta_aprobado=target.esta_aprobado,
            confianza_sugerencia=target.confianza_sugerencia,
        )

"""Approve character attribute use case.

Approves a character attribute by marking ``esta_aprobado=True`` and setting
``valor_aprobado`` to the current suggested value. Suggested values are
editable suggestions marking uncertainty; approval fixes the approved value.
Depends on injected repository protocol ports, never on concrete ORM models
or AI model implementations.
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

    async def update(  # pragma: no cover - protocol stub
        self, *, attribute_id: UUID, **kwargs: Any
    ) -> Any | None:
        """Update the attributes of the attribute with the given id."""
        ...


@dataclass(frozen=True)
class ApproveCharacterAttributeInput:
    """Input data for approving a character attribute."""

    character_id: UUID
    nombre_atributo: str


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


class ApproveCharacterAttributeUseCase:
    """Approve a character attribute.

    Marks ``esta_aprobado=True`` and sets ``valor_aprobado`` to the current
    ``valor_sugerido``. Raises ValidationError when no suggested value exists
    to approve.
    """

    def __init__(
        self,
        *,
        character_attribute_repository: CharacterAttributeRepository,
    ) -> None:
        self._character_attribute_repository = character_attribute_repository

    async def execute(self, input_data: ApproveCharacterAttributeInput) -> CharacterAttributeOutput:
        """Execute the approve character attribute use case.

        Raises:
            NotFoundError: when the attribute does not exist.
            ValidationError: when required input is missing or no suggested
                value exists to approve.
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
        if entity is None:
            raise NotFoundError(
                message="Character attribute not found.",
                details={
                    "field": "character_id",
                    "reason": "not_found",
                },
            )

        if entity.valor_sugerido is None:
            raise ValidationError(
                message="No suggested value exists to approve.",
                details={
                    "field": "valor_sugerido",
                    "reason": "missing_suggested_value",
                },
            )

        updated = await self._character_attribute_repository.update(
            attribute_id=entity.id,
            esta_aprobado=True,
            valor_aprobado=entity.valor_sugerido,
        )
        if updated is None:
            raise NotFoundError(
                message="Character attribute not found.",
                details={
                    "field": "character_id",
                    "reason": "not_found",
                },
            )

        return CharacterAttributeOutput(
            id=str(updated.id),
            character_id=str(updated.character_id),
            nombre_atributo=updated.nombre_atributo,
            valor_sugerido=updated.valor_sugerido,
            valor_aprobado=updated.valor_aprobado,
            esta_aprobado=updated.esta_aprobado,
            confianza_sugerencia=updated.confianza_sugerencia,
        )

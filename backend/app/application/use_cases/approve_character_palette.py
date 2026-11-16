"""Approve character palette use case.

Approves a character palette entry by marking ``esta_aprobado=True`` and
setting ``valor_aprobado`` to the current suggested ``valor_hex``.
Suggested color values are editable suggestions marking uncertainty; approval
fixes the approved value. Depends on injected repository protocol ports,
never on concrete ORM models or AI model implementations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from app.core.exceptions import NotFoundError, ValidationError


class CharacterPaletteRepository(Protocol):
    """Port for character palette read/write operations."""

    async def get_by_character_and_name(  # pragma: no cover - protocol stub
        self, *, character_id: UUID, nombre_color: str
    ) -> Any | None:
        """Return the palette entry for the character and name, or None."""
        ...

    async def update(  # pragma: no cover - protocol stub
        self, *, palette_id: UUID, **kwargs: Any
    ) -> Any | None:
        """Update the attributes of the palette entry with the given id."""
        ...


@dataclass(frozen=True)
class ApproveCharacterPaletteInput:
    """Input data for approving a character palette entry."""

    character_id: UUID
    nombre_color: str


@dataclass(frozen=True)
class CharacterPaletteOutput:
    """Simple output DTO for a character palette entry, never an ORM model."""

    id: str
    character_id: str
    nombre_color: str
    valor_hex: str | None
    esta_aprobado: bool


class ApproveCharacterPaletteUseCase:
    """Approve a character palette entry.

    Marks ``esta_aprobado=True`` and sets ``valor_aprobado`` to the current
    suggested ``valor_hex``. Raises ValidationError when no suggested hex
    value exists to approve.
    """

    def __init__(
        self,
        *,
        character_palette_repository: CharacterPaletteRepository,
    ) -> None:
        self._character_palette_repository = character_palette_repository

    async def execute(
        self, input_data: ApproveCharacterPaletteInput
    ) -> CharacterPaletteOutput:
        """Execute the approve character palette use case.

        Raises:
            NotFoundError: when the palette entry does not exist.
            ValidationError: when required input is missing or no suggested
                hex value exists to approve.
        """
        if not input_data.nombre_color or not input_data.nombre_color.strip():
            raise ValidationError(
                message="nombre_color is required.",
                details={
                    "field": "nombre_color",
                    "reason": "required",
                },
            )

        nombre_color = input_data.nombre_color.strip()

        entity = await self._character_palette_repository.get_by_character_and_name(
            character_id=input_data.character_id,
            nombre_color=nombre_color,
        )
        if entity is None:
            raise NotFoundError(
                message="Character palette entry not found.",
                details={
                    "field": "character_id",
                    "reason": "not_found",
                },
            )

        if entity.valor_hex is None:
            raise ValidationError(
                message="No suggested hex value exists to approve.",
                details={
                    "field": "valor_hex",
                    "reason": "missing_suggested_value",
                },
            )

        updated = await self._character_palette_repository.update(
            palette_id=entity.id,
            esta_aprobado=True,
            valor_hex=entity.valor_hex,
        )
        if updated is None:
            raise NotFoundError(
                message="Character palette entry not found.",
                details={
                    "field": "character_id",
                    "reason": "not_found",
                },
            )

        return CharacterPaletteOutput(
            id=str(updated.id),
            character_id=str(updated.character_id),
            nombre_color=updated.nombre_color,
            valor_hex=updated.valor_hex,
            esta_aprobado=updated.esta_aprobado,
        )

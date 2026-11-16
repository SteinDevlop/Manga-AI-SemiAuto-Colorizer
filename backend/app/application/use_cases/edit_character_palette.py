"""Edit character palette use case.

Updates or creates a character palette entry (e.g. base color, shadow, light).
The color value is an editable suggestion marking uncertainty; it is never an
official color. Depends on injected repository protocol ports, never on
concrete ORM models or AI model implementations.
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

    async def create(  # pragma: no cover - protocol stub
        self, **kwargs: Any
    ) -> Any:
        """Create and persist a new palette entry from the given attributes."""
        ...

    async def update(  # pragma: no cover - protocol stub
        self, *, palette_id: UUID, **kwargs: Any
    ) -> Any | None:
        """Update the attributes of the palette entry with the given id."""
        ...


@dataclass(frozen=True)
class EditCharacterPaletteInput:
    """Input data for editing a character palette entry."""

    character_id: UUID
    nombre_color: str
    valor_hex: str | None = None


@dataclass(frozen=True)
class CharacterPaletteOutput:
    """Simple output DTO for a character palette entry, never an ORM model."""

    id: str
    character_id: str
    nombre_color: str
    valor_hex: str | None
    esta_aprobado: bool


class EditCharacterPaletteUseCase:
    """Update or create a character palette entry.

    The color value is an editable suggestion marking uncertainty; it never
    constitutes an official color. The entry is created when it does not
    exist yet, otherwise it is updated in place.
    """

    def __init__(
        self,
        *,
        character_palette_repository: CharacterPaletteRepository,
    ) -> None:
        self._character_palette_repository = character_palette_repository

    async def execute(self, input_data: EditCharacterPaletteInput) -> CharacterPaletteOutput:
        """Execute the edit character palette use case.

        Raises:
            NotFoundError: when the character cannot be located.
            ValidationError: when required input is missing or invalid.
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

        if entity is not None:
            updates: dict[str, Any] = {"nombre_color": nombre_color}
            if input_data.valor_hex is not None:
                updates["valor_hex"] = input_data.valor_hex

            updated = await self._character_palette_repository.update(
                palette_id=entity.id,
                **updates,
            )
            if updated is None:
                raise NotFoundError(
                    message="Character palette entry not found.",
                    details={
                        "field": "character_id",
                        "reason": "not_found",
                    },
                )
            target = updated
        else:
            target = await self._character_palette_repository.create(
                character_id=input_data.character_id,
                nombre_color=nombre_color,
                valor_hex=input_data.valor_hex,
                esta_aprobado=False,
            )

        return CharacterPaletteOutput(
            id=str(target.id),
            character_id=str(target.character_id),
            nombre_color=target.nombre_color,
            valor_hex=target.valor_hex,
            esta_aprobado=target.esta_aprobado,
        )

"""List character appearances use case.

Returns all appearances of a character with their panels and pages.
Depends on repository ports only, never on ORM models or AI model
implementations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from app.core.exceptions import NotFoundError


class CharacterAppearanceRepository(Protocol):
    """Port for character appearance read operations."""

    async def list_by_character(  # pragma: no cover - protocol stub
        self, *, character_id: UUID
    ) -> list[Any]:
        """Return all appearances of the given character."""
        ...


@dataclass(frozen=True)
class CharacterAppearanceOutput:
    """Simple output DTO for a character appearance, never an ORM model.

    Includes the related page and panel identifiers when available.
    """

    id: str
    character_id: str
    page_id: str
    panel_id: str | None
    confianza_deteccion: float | None
    page_number: int | None
    panel_number: int | None
    created_at: str | None


@dataclass(frozen=True)
class ListCharacterAppearancesOutput:
    """Simple output DTO with the appearances of a character."""

    character_id: str
    appearances: list[CharacterAppearanceOutput]
    total: int


class ListCharacterAppearancesUseCase:
    """List all appearances of a character with their panels and pages."""

    def __init__(
        self,
        character_appearance_repository: CharacterAppearanceRepository,
    ) -> None:
        self._character_appearance_repository = character_appearance_repository

    async def execute(
        self, character_id: UUID
    ) -> ListCharacterAppearancesOutput:
        """Execute the list character appearances use case.

        Raises:
            NotFoundError: when no appearances exist for the character.
        """
        appearances = await self._character_appearance_repository.list_by_character(
            character_id=character_id
        )

        if not appearances:
            raise NotFoundError(
                message="No appearances found for the given character.",
                details={"field": "character_id", "reason": "not_found"},
            )

        dto_appearances: list[CharacterAppearanceOutput] = []
        for appearance in appearances:
            page = getattr(appearance, "page", None)
            panel = getattr(appearance, "panel", None)
            page_number = getattr(page, "numero_orden", None) if page is not None else None
            panel_number = getattr(panel, "numero_orden", None) if panel is not None else None
            dto_appearances.append(
                CharacterAppearanceOutput(
                    id=str(appearance.id),
                    character_id=str(appearance.character_id),
                    page_id=str(appearance.page_id),
                    panel_id=(
                        str(appearance.panel_id) if appearance.panel_id else None
                    ),
                    confianza_deteccion=appearance.confianza_deteccion,
                    page_number=page_number,
                    panel_number=panel_number,
                    created_at=appearance.created_at.isoformat()
                    if appearance.created_at
                    else None,
                )
            )

        return ListCharacterAppearancesOutput(
            character_id=str(character_id),
            appearances=dto_appearances,
            total=len(dto_appearances),
        )

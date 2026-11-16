"""Review character identity use case.

Allows a user to confirm or correct the identity of a character appearance
(human-in-the-loop, ADR-005) by assigning it to an existing character.
Depends on injected repository protocol ports, never on concrete ORM models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from app.core.exceptions import NotFoundError, ValidationError


class CharacterAppearanceRepository(Protocol):
    """Port for character appearance read/write operations."""

    async def get(self, *, appearance_id: UUID) -> Any:  # pragma: no cover - protocol stub
        """Return the appearance with the given ID, or None when not found."""
        ...

    async def update_character(  # pragma: no cover - protocol stub
        self, *, appearance_id: UUID, character_id: UUID
    ) -> Any:
        """Assign a character to an appearance, returning it or None when absent."""
        ...


class CharacterRepository(Protocol):
    """Port for character read operations."""

    async def get(self, *, character_id: UUID) -> Any:  # pragma: no cover - protocol stub
        """Return the character with the given ID, or None when not found."""
        ...


@dataclass(frozen=True)
class ReviewIdentityInput:
    """Input data for reviewing the identity of an appearance."""

    appearance_id: UUID
    character_id: UUID | None = None


@dataclass(frozen=True)
class AppearanceOutput:
    """Simple output DTO for a character appearance, never an ORM model."""

    id: str
    page_id: str
    character_id: str
    panel_id: str | None
    confianza_deteccion: float | None
    created_at: str


class ReviewIdentityUseCase:
    """Confirm or correct the identity of a character appearance.

    When ``character_id`` is provided, the appearance is assigned to that
    character after confirming both the appearance and the character exist.
    When omitted, the request is invalid because an identity must be
    explicitly assigned (human-in-the-loop, ADR-005).
    """

    def __init__(
        self,
        *,
        appearance_repository: CharacterAppearanceRepository,
        character_repository: CharacterRepository,
    ) -> None:
        self._appearance_repository = appearance_repository
        self._character_repository = character_repository

    async def execute(self, input_data: ReviewIdentityInput) -> AppearanceOutput:
        """Execute the review identity use case.

        Raises:
            ValidationError: when no character_id is provided.
            NotFoundError: when the appearance or character does not exist.
        """
        if input_data.character_id is None:
            raise ValidationError(
                message="character_id is required to confirm or correct an identity.",
                details={"field": "character_id", "reason": "required"},
            )

        appearance = await self._appearance_repository.get(
            appearance_id=input_data.appearance_id,
        )
        if appearance is None:
            raise NotFoundError(
                message="Character appearance not found.",
                details={"field": "appearance_id", "reason": "not_found"},
            )

        character = await self._character_repository.get(
            character_id=input_data.character_id,
        )
        if character is None:
            raise NotFoundError(
                message="Character not found.",
                details={"field": "character_id", "reason": "not_found"},
            )

        updated = await self._appearance_repository.update_character(
            appearance_id=input_data.appearance_id,
            character_id=input_data.character_id,
        )
        if updated is None:
            raise NotFoundError(
                message="Character appearance not found.",
                details={"field": "appearance_id", "reason": "not_found"},
            )

        return AppearanceOutput(
            id=str(updated.id),
            page_id=str(updated.page_id),
            character_id=str(updated.character_id),
            panel_id=str(updated.panel_id) if updated.panel_id is not None else None,
            confianza_deteccion=updated.confianza_deteccion,
            created_at=updated.created_at.isoformat(),
        )

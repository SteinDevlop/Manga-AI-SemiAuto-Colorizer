"""Group character identities use case.

Groups the character appearances of a page analysis into stable identities
using an injected ``CharacterMatcher`` protocol, and persists the grouping
(``CharacterAppearance.character_id``) through repository ports.
Never depends on concrete AI model implementations or ORM models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from app.ai_engine.contracts import CharacterMatcher
from app.core.exceptions import NotFoundError, ValidationError


class AnalysisRepository(Protocol):
    """Port for analysis read operations."""

    async def get(self, *, analysis_id: UUID) -> Any:  # pragma: no cover - protocol stub
        """Return the analysis with the given ID, or None when not found."""
        ...


class CharacterAppearanceRepository(Protocol):
    """Port for character appearance read/write operations."""

    async def list_by_page(self, *, page_id: UUID) -> list[Any]:  # pragma: no cover - protocol stub
        """Return all appearances of the given page, ordered by creation time."""
        ...

    async def update_character(  # pragma: no cover - protocol stub
        self, *, appearance_id: UUID, character_id: UUID
    ) -> Any:
        """Assign a character to an appearance, returning it or None when absent."""
        ...


class CharacterRepository(Protocol):
    """Port for character write operations."""

    async def create(  # pragma: no cover - protocol stub
        self,
        *,
        nombre: str,
        descripcion: str | None,
        confianza_identidad: float | None,
    ) -> Any:
        """Create and persist a character, returning the persisted entity."""
        ...


@dataclass(frozen=True)
class GroupIdentitiesInput:
    """Input data for grouping the identities of an analysis."""

    analysis_id: UUID


@dataclass(frozen=True)
class GroupedIdentity:
    """One grouped identity with its appearances and matching confidence."""

    character_id: str
    nombre: str
    confianza_identidad: float | None
    appearance_ids: list[str]


@dataclass(frozen=True)
class GroupIdentitiesOutput:
    """Simple output DTO with the grouped identities of an analysis."""

    analysis_id: str
    identities: list[GroupedIdentity]
    total_appearances: int


class GroupIdentitiesUseCase:
    """Group the character appearances of an analysis into stable identities.

    Depends on injected protocol ports only: an analysis repository, a
    character appearance repository, a character repository, and the
    ``CharacterMatcher`` protocol from the AI engine contracts. No concrete
    AI model or ORM model is referenced.
    """

    def __init__(
        self,
        *,
        analysis_repository: AnalysisRepository,
        appearance_repository: CharacterAppearanceRepository,
        character_repository: CharacterRepository,
        matcher: CharacterMatcher,
    ) -> None:
        self._analysis_repository = analysis_repository
        self._appearance_repository = appearance_repository
        self._character_repository = character_repository
        self._matcher = matcher

    async def execute(self, input_data: GroupIdentitiesInput) -> GroupIdentitiesOutput:
        """Execute the group identities use case.

        Raises:
            NotFoundError: when no analysis matches the given ID.
            ValidationError: when the matcher returns a malformed proposal.
        """
        analysis = await self._analysis_repository.get(analysis_id=input_data.analysis_id)
        if analysis is None:
            raise NotFoundError(
                message="Analysis not found.",
                details={"field": "analysis_id", "reason": "not_found"},
            )

        appearances = await self._appearance_repository.list_by_page(
            page_id=analysis.page_id,
        )

        proposals = self._matcher.match(
            appearances=[
                {"id": str(appearance.id), "confianza": appearance.confianza_deteccion}
                for appearance in appearances
            ],
        )

        identities: list[GroupedIdentity] = []
        for proposal in proposals:
            appearance_ids = proposal.get("apariciones", [])
            confianza_raw = proposal.get("confianza_identidad")
            nombre_raw = proposal.get("nombre_sugerido")

            if not isinstance(appearance_ids, list) or not appearance_ids:
                raise ValidationError(
                    message="Matcher returned a proposal without appearances.",
                    details={"field": "apariciones", "reason": "invalid_proposal"},
                )

            confianza = (
                float(confianza_raw)
                if isinstance(confianza_raw, (int, float)) and not isinstance(confianza_raw, bool)
                else None
            )
            nombre = str(nombre_raw) if nombre_raw else f"Character {len(identities) + 1}"

            character = await self._character_repository.create(
                nombre=nombre,
                descripcion=None,
                confianza_identidad=confianza,
            )

            for appearance_id in appearance_ids:
                await self._appearance_repository.update_character(
                    appearance_id=UUID(str(appearance_id)),
                    character_id=character.id,
                )

            identities.append(
                GroupedIdentity(
                    character_id=str(character.id),
                    nombre=nombre,
                    confianza_identidad=confianza,
                    appearance_ids=[str(appearance_id) for appearance_id in appearance_ids],
                )
            )

        return GroupIdentitiesOutput(
            analysis_id=str(input_data.analysis_id),
            identities=identities,
            total_appearances=len(appearances),
        )

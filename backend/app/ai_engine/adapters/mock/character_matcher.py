"""Mock character matcher adapter.

Implements the ``CharacterMatcher`` protocol by grouping all appearances
into a single identity with high confidence. No inference is performed.
"""

from __future__ import annotations

from typing import TypedDict


class IdentityProposal(TypedDict):
    """Serialized identity-matching proposal."""

    apariciones: list[str]
    confianza_identidad: float
    nombre_sugerido: str


class MockCharacterMatcher:
    """Mock implementation of :class:`CharacterMatcher`.

    Groups every provided appearance into one stable identity with high
    confidence. No feature extraction or inference is performed.
    """

    FIXED_CONFIDENCE: float = 0.96
    DEFAULT_NAME: str = "protagonista"

    def match(self, appearances: list[dict]) -> list[IdentityProposal]:
        """Return a single identity proposal grouping all appearances.

        Args:
            appearances: Character appearance detections. Each may carry an
                ``id``; otherwise a positional id is synthesized.

        Returns:
            A list with one proposal containing all appearance ids, or an
            empty list when there are no appearances.
        """
        if not appearances:
            return []

        appearance_ids = [
            str(appearance.get("id", f"aparicion-{index}"))
            for index, appearance in enumerate(appearances, start=1)
        ]
        return [
            IdentityProposal(
                apariciones=appearance_ids,
                confianza_identidad=self.FIXED_CONFIDENCE,
                nombre_sugerido=self.DEFAULT_NAME,
            )
        ]

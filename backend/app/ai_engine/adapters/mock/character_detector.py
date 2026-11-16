"""Mock character detector adapter.

Implements the ``CharacterDetector`` protocol with fixed, fictional results.
No heavy inference is executed in this phase (the real model lands in P8).
"""

from __future__ import annotations

from typing import TypedDict


class CharacterDetection(TypedDict):
    """Serialized character appearance detection result."""

    x: int
    y: int
    ancho: int
    alto: int
    confianza: float
    etiqueta: str


class MockCharacterDetector:
    """Mock implementation of :class:`CharacterDetector`.

    Returns 1-2 fictional character appearances with bounding boxes and
    fixed confidence. The ``min_confidence`` argument is accepted for
    protocol compatibility; the mock always returns the same fixed results.
    """

    FIXED_CONFIDENCE: float = 0.88

    def detect(
        self,
        image_path: str,
        *,
        min_confidence: float = 0.0,
    ) -> list[CharacterDetection]:
        """Return fictional character appearances for the given image.

        Args:
            image_path: Path to the image (unused by the mock).
            min_confidence: Minimum confidence threshold (unused by the mock).

        Returns:
            A list of 1-2 fictional character appearances with bounding
            boxes and fixed confidence.
        """
        del image_path, min_confidence
        return [
            CharacterDetection(
                x=120,
                y=200,
                ancho=90,
                alto=160,
                confianza=self.FIXED_CONFIDENCE,
                etiqueta="personaje",
            ),
            CharacterDetection(
                x=450,
                y=180,
                ancho=80,
                alto=150,
                confianza=0.85,
                etiqueta="personaje",
            ),
        ]

"""Mock panel detector adapter.

Implements the ``PanelDetector`` protocol with fixed, fictional results.
No heavy inference is executed in this phase (the real model lands in P8).
"""

from __future__ import annotations

from typing import TypedDict


class Panel(TypedDict):
    """Serialized panel detection result."""

    numero_orden: int
    x: int
    y: int
    ancho: int
    alto: int
    confianza: float


class MockPanelDetector:
    """Mock implementation of :class:`PanelDetector`.

    Returns 1-3 fictional panels with bounding boxes and fixed confidence.
    The ``min_confidence`` argument is accepted for protocol compatibility;
    the mock always returns the same fixed results.
    """

    FIXED_CONFIDENCE: float = 0.92

    def detect(
        self,
        image_path: str,
        *,
        min_confidence: float = 0.0,
    ) -> list[Panel]:
        """Return fictional panels for the given page image.

        Args:
            image_path: Path to the page image (unused by the mock).
            min_confidence: Minimum confidence threshold (unused by the mock).

        Returns:
            A list of 1-3 fictional panels with bounding boxes and fixed
            confidence.
        """
        del image_path, min_confidence
        return [
            Panel(
                numero_orden=1,
                x=40,
                y=40,
                ancho=320,
                alto=240,
                confianza=self.FIXED_CONFIDENCE,
            ),
            Panel(
                numero_orden=2,
                x=380,
                y=40,
                ancho=320,
                alto=240,
                confianza=self.FIXED_CONFIDENCE,
            ),
            Panel(
                numero_orden=3,
                x=210,
                y=300,
                ancho=240,
                alto=180,
                confianza=self.FIXED_CONFIDENCE,
            ),
        ]

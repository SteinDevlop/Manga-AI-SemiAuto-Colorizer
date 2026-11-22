"""Mock character detector adapter.

Implements the ``CharacterDetector`` protocol with variable fictional results
derived from the image content hash. No heavy inference is executed in this
phase (the real model lands in P8).
"""

from __future__ import annotations

import hashlib
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

    Returns 1-3 fictional character appearances with bounding boxes.
    Position and size are derived deterministically from the image path hash,
    simulating varied detection results without requiring a real model.
    """

    def detect(
        self,
        image_path: str,
        *,
        min_confidence: float = 0.0,
    ) -> list[CharacterDetection]:
        """Return fictional character appearances for the given image.

        Args:
            image_path: Path to the image. The hash of this path seeds
                deterministic but varied bounding box results.
            min_confidence: Minimum confidence threshold (unused by the mock).

        Returns:
            A list of 1-3 fictional character appearances with bounding
            boxes and varying confidence. Each run with the same image path
            returns identical results.
        """
        del min_confidence
        # Seed deterministic variation from image path hash
        h = int(hashlib.md5(image_path.encode()).hexdigest()[:8], 16)
        n = 1 + (h % 3)  # 1, 2, or 3 detections

        results: list[CharacterDetection] = []
        img_w, img_h = 800, 1000  # assumed page size; adapt if needed

        for i in range(n):
            # Spread detections across the page using hash-derived values
            x = ((h >> (8 * i)) % (img_w - 200)) + 50
            y = ((h >> (8 * (i + 1))) % (img_h - 300)) + 50
            w = 150 + (h % (img_w - 300))
            hh = 200 + (h % (img_h - 400))
            # Clamp to image bounds
            x = max(0, min(x, img_w - w - 10))
            y = max(0, min(y, img_h - hh - 10))
            conf = 0.5 + (h % 100) / 200.0  # 0.5..1.49
            results.append(
                CharacterDetection(
                    x=x,
                    y=y,
                    ancho=w,
                    alto=hh,
                    confianza=round(conf, 2),
                    etiqueta="personaje",
                )
            )
        return results

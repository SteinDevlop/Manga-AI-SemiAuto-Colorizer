"""Mock segmenter adapter.

Implements the ``Segmenter`` protocol with fictional mask artifacts.
No heavy inference is executed here; the real model lands in P8.
"""

from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path
from typing import TypedDict


class MaskArtifact(TypedDict):
    """Serialized mask artifact produced by the segmenter."""

    region_id: str
    ruta_archivo: str
    hash_sha256: str
    ancho: int
    alto: int
    tipo_mascara: str


class MockSegmenter:
    """Mock implementation of :class:`Segmenter`.

    Returns one fictional mask artifact per requested region: a simulated
    file path and a simulated SHA-256 hash derived deterministically from
    the image path and region identifier. No image inference is performed.
    """

    DEFAULT_WIDTH: int = 256
    DEFAULT_HEIGHT: int = 256
    DEFAULT_MASK_TYPE: str = "personaje"

    def segment(
        self,
        image_path: str,
        *,
        regions: list[dict],
    ) -> list[MaskArtifact]:
        """Return a fictional mask artifact for each requested region.

        Args:
            image_path: Path to the source image. It is only used to seed
                the simulated hash; no inference is performed on it.
            regions: Regions to mask. Each entry is a dict that may carry a
                ``region_id``; a positional id is synthesized otherwise.

        Returns:
            A list of mask artifacts, one per input region.
        """
        masks: list[MaskArtifact] = []
        for index, region in enumerate(regions, start=1):
            region_id = str(region.get("region_id", f"region-{index}"))
            digest = hashlib.sha256(f"{image_path}:{region_id}".encode("utf-8")).hexdigest()

            # Create a temporary empty PNG file so the storage service can read it.
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            tmp.close()
            Path(tmp.name).touch()

            masks.append(
                MaskArtifact(
                    region_id=region_id,
                    ruta_archivo=tmp.name,
                    hash_sha256=digest,
                    ancho=self.DEFAULT_WIDTH,
                    alto=self.DEFAULT_HEIGHT,
                    tipo_mascara=self.DEFAULT_MASK_TYPE,
                )
            )
        return masks

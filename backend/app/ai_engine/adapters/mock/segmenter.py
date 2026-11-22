"""Mock segmenter adapter.

Implements the ``Segmenter`` protocol with mask artifacts generated from
character detection regions. No heavy inference is executed in this phase
(the real model lands in P8).
"""

from __future__ import annotations

import hashlib
import os
from typing import TypedDict

import cv2
import numpy as np


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

    Generates mask artifacts by creating binary masks from the character
    detection bounding boxes. Each mask is saved as a PNG file so that
    downstream stages (e.g., colorization hint channels) can consume them.
    """

    def segment(
        self,
        image_path: str,
        *,
        regions: list[dict],
    ) -> list[MaskArtifact]:
        """Return mask artifacts generated from character detection regions.

        For each region a binary mask PNG is created (white rectangle on
        black background) and saved to a temporary path. The mask covers the
        full bounding box specified by the region dict.

        Args:
            image_path: Path to the source image. Used only to derive a
                deterministic temp directory; the actual image is not read.
            regions: List of region dicts, each expected to contain at least:
                - ``region_id``: str
                - ``x``, ``y``, ``ancho``, ``alto``: bounding box in pixels

        Returns:
            A list of mask artifacts, one per input region. Each artifact
            includes the path to the saved PNG mask file.
        """
        # Use a deterministic temp dir under the system temp dir
        tmp_dir = os.path.join("/tmp", "manga_colorizer_masks")
        os.makedirs(tmp_dir, exist_ok=True)

        # Assumed page size; in a real system this would come from actually
        # reading the image dimensions.
        page_h, page_w = 1000, 800

        results: list[MaskArtifact] = []
        for region in regions:
            region_id = region.get("region_id", f"region-{len(results)}")
            x = max(0, min(int(region.get("x", 0)), page_w - 1))
            y = max(0, min(int(region.get("y", 0)), page_h - 1))
            w_box = max(
                1,
                min(int(region.get("ancho", 100)), page_w - x),
            )
            hh = max(
                1,
                min(int(region.get("alto", 100)), page_h - y),
            )

            # Create binary mask: white rect on black background
            mask = np.zeros((page_h, page_w), dtype=np.uint8)
            mask[y : y + hh, x : x + w_box] = 255

            # Save mask PNG
            mask_filename = f"{region_id}.png"
            mask_path = os.path.join(tmp_dir, mask_filename)
            cv2.imwrite(mask_path, mask)

            # Compute SHA-256 of the mask file content
            with open(mask_path, "rb") as _f:
                file_hash = hashlib.sha256(_f.read()).hexdigest()

            results.append(
                MaskArtifact(
                    region_id=region_id,
                    ruta_archivo=mask_path,
                    hash_sha256=file_hash,
                    ancho=w_box,
                    alto=hh,
                    tipo_mascara="character",
                )
            )
        return results

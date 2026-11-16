"""Real segmenter adapter (placeholder).

Implements the ``Segmenter`` protocol. Attempts to load a real
segmentation model; when the model is unavailable it records the error and
every subsequent :meth:`segment` call raises
:class:`ModelUnavailableError` with a clear message. No heavy inference is
executed here (the real model lands in P8/future).
"""

from __future__ import annotations

from typing import TypedDict

from . import ModelUnavailableError


class MaskArtifact(TypedDict):
    """Serialized mask artifact produced by the segmenter."""

    region_id: str
    ruta_archivo: str
    hash_sha256: str
    ancho: int
    alto: int
    tipo_mascara: str


class RealSegmenter:
    """Real placeholder implementation of :class:`Segmenter`.

    The constructor calls :meth:`load_model`, which attempts to load the
    real segmentation model. When loading fails (missing weights, no GPU,
    etc.) the error is stored and every later :meth:`segment` call raises
    :class:`ModelUnavailableError` with a clear message.
    """

    MODEL_NAME: str = "segmenter"
    MODEL_PATH: str = "models/segmenter.pt"

    def __init__(self) -> None:
        self._model: object | None = None
        self._load_error: str | None = None
        self._loaded: bool = False
        self.load_model()

    def load_model(self) -> bool:
        """Attempt to load the real segmentation model.

        Returns:
            ``True`` when the model was loaded, ``False`` otherwise. On
            failure the error is stored and no exception is raised here;
            subsequent :meth:`segment` calls raise
            :class:`ModelUnavailableError`.
        """
        try:
            self._load_real_model()
        except Exception as exc:  # noqa: BLE001 - report any load failure
            self._loaded = False
            self._model = None
            self._load_error = f"{type(exc).__name__}: {exc}"
            return False
        self._loaded = True
        return True

    def _load_real_model(self) -> None:
        """Attempt to load the real model weights (placeholder).

        No real model exists yet in this phase, so this intentionally
        raises :class:`FileNotFoundError` to surface that the weights are
        missing instead of failing silently.
        """
        raise FileNotFoundError(f"Segmenter weights not found at {self.MODEL_PATH}")

    def _ensure_loaded(self) -> None:
        if not self._loaded or self._model is None:
            raise ModelUnavailableError(
                self.MODEL_NAME,
                self._load_error or "model not loaded",
            )

    def segment(
        self,
        image_path: str,
        *,
        regions: list[dict],
    ) -> list[MaskArtifact]:
        """Return mask artifacts for each requested region.

        Args:
            image_path: Path to the source image.
            regions: Regions to mask.

        Returns:
            A list of mask artifacts, one per input region.

        Raises:
            ModelUnavailableError: When the real model is not available.
        """
        self._ensure_loaded()
        del image_path, regions  # placeholder: no inference yet
        return []

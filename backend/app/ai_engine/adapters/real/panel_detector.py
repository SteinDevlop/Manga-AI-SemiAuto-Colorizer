"""Real panel detector adapter (placeholder).

Implements the ``PanelDetector`` protocol. Attempts to load a real panel
detection model; when the model is unavailable it records the error and
every subsequent :meth:`detect` call raises :class:`ModelUnavailableError`
with a clear message. No heavy inference is executed here (the real model
lands in P8/future).
"""

from __future__ import annotations

from typing import TypedDict

from . import ModelUnavailableError


class Panel(TypedDict):
    """Serialized panel detection result."""

    numero_orden: int
    x: int
    y: int
    ancho: int
    alto: int
    confianza: float


class RealPanelDetector:
    """Real placeholder implementation of :class:`PanelDetector`.

    The constructor calls :meth:`load_model`, which attempts to load the
    real panel detection model. When loading fails (missing weights, no
    GPU, etc.) the error is stored and every later :meth:`detect` call
    raises :class:`ModelUnavailableError` with a clear message.
    """

    MODEL_NAME: str = "panel-detector"
    MODEL_PATH: str = "models/panel_detector.pt"

    def __init__(self) -> None:
        self._model: object | None = None
        self._load_error: str | None = None
        self._loaded: bool = False
        self.load_model()

    def load_model(self) -> bool:
        """Attempt to load the real panel detection model.

        Returns:
            ``True`` when the model was loaded, ``False`` otherwise. On
            failure the error is stored and no exception is raised here;
            subsequent :meth:`detect` calls raise
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
        raise FileNotFoundError(
            f"Panel detector weights not found at {self.MODEL_PATH}"
        )

    def _ensure_loaded(self) -> None:
        if not self._loaded or self._model is None:
            raise ModelUnavailableError(
                self.MODEL_NAME,
                self._load_error or "model not loaded",
            )

    def detect(
        self,
        image_path: str,
        *,
        min_confidence: float = 0.0,
    ) -> list[Panel]:
        """Return panel detections for the given page image.

        Args:
            image_path: Path to the page image.
            min_confidence: Minimum confidence threshold.

        Returns:
            A list of panels with bounding boxes, order and confidence.

        Raises:
            ModelUnavailableError: When the real model is not available.
        """
        self._ensure_loaded()
        del image_path, min_confidence  # placeholder: no inference yet
        return []

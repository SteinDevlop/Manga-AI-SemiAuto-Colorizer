"""Real character detector adapter (placeholder).

Implements the ``CharacterDetector`` protocol. Attempts to load a real
character detection model; when the model is unavailable it records the
error and every subsequent :meth:`detect` call raises
:class:`ModelUnavailableError` with a clear message. No heavy inference is
executed here (the real model lands in P8/future).
"""

from __future__ import annotations

from typing import TypedDict

from app.ai_engine.contracts import CharacterDetector
from . import ModelUnavailableError


class CharacterDetection(TypedDict):
    """Serialized character appearance detection result."""

    x: int
    y: int
    ancho: int
    alto: int
    confianza: float
    etiqueta: str


class RealCharacterDetector:
    """Real placeholder implementation of :class:`CharacterDetector`.

    The constructor calls :meth:`load_model`, which attempts to load the
    real character detection model. When loading fails (missing weights,
    no GPU, etc.) the error is stored and every later :meth:`detect` call
    raises :class:`ModelUnavailableError` with a clear message.
    """

    MODEL_NAME: str = "character-detector"
    MODEL_PATH: str = "models/character_detector.pt"

    def __init__(self) -> None:
        self._model: object | None = None
        self._load_error: str | None = None
        self._loaded: bool = False
        self.load_model()

    def load_model(self) -> bool:
        """Attempt to load the real character detection model.

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
            f"Character detector weights not found at {self.MODEL_PATH}"
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
    ) -> list[CharacterDetection]:
        """Return character detections for the given image.

        Args:
            image_path: Path to the image.
            min_confidence: Minimum confidence threshold.

        Returns:
            A list of character appearances with bounding boxes and labels.

        Raises:
            ModelUnavailableError: When the real model is not available.
        """
        self._ensure_loaded()
        del image_path, min_confidence  # placeholder: no inference yet
        return []

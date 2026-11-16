"""Real colorization engine adapter (placeholder).

Implements the ``ColorizationEngine`` protocol. Attempts to load a real
colorization model; when the model is unavailable it records the error and
every subsequent :meth:`colorize` call raises :class:`ModelUnavailableError`
with a clear message. No heavy inference is executed here (the real model
lands in P8/future).
"""

from __future__ import annotations

from typing import TypedDict

from app.ai_engine.contracts import ColorizationEngine
from . import ModelUnavailableError


class ColorizationResult(TypedDict):
    """Serialized colorization result."""

    ruta_resultado: str
    version_modelo: str
    parametros: dict


class RealColorizationEngine:
    """Real placeholder implementation of :class:`ColorizationEngine`.

    The constructor calls :meth:`load_model`, which attempts to load the
    real colorization model. When loading fails (missing weights, no GPU,
    etc.) the error is stored and every later :meth:`colorize` call raises
    :class:`ModelUnavailableError` with a clear message.
    """

    MODEL_NAME: str = "colorization-engine"
    MODEL_PATH: str = "models/colorization_engine.pt"

    def __init__(self) -> None:
        self._model: object | None = None
        self._load_error: str | None = None
        self._loaded: bool = False
        self.load_model()

    def load_model(self) -> bool:
        """Attempt to load the real colorization model.

        Returns:
            ``True`` when the model was loaded, ``False`` otherwise. On
            failure the error is stored and no exception is raised here;
            subsequent :meth:`colorize` calls raise
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
            f"Colorization engine weights not found at {self.MODEL_PATH}"
        )

    def _ensure_loaded(self) -> None:
        if not self._loaded or self._model is None:
            raise ModelUnavailableError(
                self.MODEL_NAME,
                self._load_error or "model not loaded",
            )

    def colorize(
        self,
        *,
        image_path: str,
        mask_references: list[str],
        palette: dict,
    ) -> ColorizationResult:
        """Return a colorization result for the given image and masks.

        Args:
            image_path: Path to the source image.
            mask_references: Paths to the mask reference images.
            palette: Color palette to apply.

        Returns:
            A dict with the result path, model version and parameters.

        Raises:
            ModelUnavailableError: When the real model is not available.
        """
        self._ensure_loaded()
        del image_path, mask_references, palette  # placeholder: no inference yet
        return ColorizationResult(
            ruta_resultado="",
            version_modelo=self.MODEL_NAME,
            parametros={},
        )

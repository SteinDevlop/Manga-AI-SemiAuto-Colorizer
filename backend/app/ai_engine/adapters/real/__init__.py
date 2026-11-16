"""Real AI engine adapters (placeholders for the future model).

Placeholder implementations of the Protocols in ``app.ai_engine.contracts``.
Each adapter attempts to load a real model; when the model is unavailable
it records the error and every subsequent call raises
:class:`ModelUnavailableError` with a clear message. No heavy inference is
executed here (the real model lands in P8/future).
"""

from __future__ import annotations


class ModelUnavailableError(RuntimeError):
    """Raised when a real AI model is not available for inference.

    Attributes:
        model_name: Name of the model that could not be loaded.
        reason: Human-readable reason why the model is unavailable.
    """

    def __init__(self, model_name: str, reason: str) -> None:
        self.model_name = model_name
        self.reason = reason
        super().__init__(
            f"Model '{model_name}' is unavailable: {reason}"
        )


# NOTE: ModelUnavailableError is defined above the submodule imports so that
# each adapter can do ``from . import ModelUnavailableError`` while the
# ``real`` package is still being initialized (no circular-import failure).

from .character_detector import RealCharacterDetector  # noqa: E402
from .character_matcher import RealCharacterMatcher  # noqa: E402
from .colorization_engine import RealColorizationEngine  # noqa: E402
from .panel_detector import RealPanelDetector  # noqa: E402
from .segmenter import RealSegmenter  # noqa: E402

__all__ = [
    "ModelUnavailableError",
    "RealCharacterDetector",
    "RealCharacterMatcher",
    "RealColorizationEngine",
    "RealPanelDetector",
    "RealSegmenter",
]

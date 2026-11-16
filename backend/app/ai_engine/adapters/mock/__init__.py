"""Mock adapters for the AI engine (phase P4).

Stub implementations of the Protocols in ``app.ai_engine.contracts``.
No heavy inference is executed here; the real model is integrated in P8.
"""

from .character_detector import MockCharacterDetector
from .character_matcher import MockCharacterMatcher
from .panel_detector import MockPanelDetector
from .segmenter import MockSegmenter

__all__ = [
    "MockCharacterDetector",
    "MockCharacterMatcher",
    "MockPanelDetector",
    "MockSegmenter",
]

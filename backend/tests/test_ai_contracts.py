"""RED/GREEN tests for P4 AI engine contracts (S1).

Verifies that Protocol definitions exist, are runtime_checkable, and
have the expected method signatures.
"""

import inspect

from app.ai_engine.contracts import (
    CharacterDetector,
    CharacterMatcher,
    ColorizationEngine,
    PanelDetector,
    Segmenter,
)


def test_protocols_are_runtime_checkable():
    """Todos los Protocolos deben ser runtime_checkable para isinstance."""
    for proto in (
        CharacterDetector,
        CharacterMatcher,
        ColorizationEngine,
        PanelDetector,
        Segmenter,
    ):
        assert hasattr(proto, "_is_runtime_protocol")


def test_character_detector_signature():
    """CharacterDetector debe tener detect(image_path, min_confidence)."""
    sig = inspect.signature(CharacterDetector.detect)
    params = list(sig.parameters.keys())
    assert "self" in params
    assert "image_path" in params
    assert "min_confidence" in params


def test_panel_detector_signature():
    """PanelDetector debe tener detect(image_path, min_confidence)."""
    sig = inspect.signature(PanelDetector.detect)
    params = list(sig.parameters.keys())
    assert "self" in params
    assert "image_path" in params
    assert "min_confidence" in params


def test_segmenter_signature():
    """Segmenter debe tener segment(image_path, regions)."""
    sig = inspect.signature(Segmenter.segment)
    params = list(sig.parameters.keys())
    assert "self" in params
    assert "image_path" in params
    assert "regions" in params


def test_character_matcher_signature():
    """CharacterMatcher debe tener match(appearances)."""
    sig = inspect.signature(CharacterMatcher.match)
    params = list(sig.parameters.keys())
    assert "self" in params
    assert "appearances" in params


def test_colorization_engine_signature():
    """ColorizationEngine debe tener colorize con kwargs nombrados."""
    sig = inspect.signature(ColorizationEngine.colorize)
    params = list(sig.parameters.keys())
    assert "self" in params
    assert "image_path" in params
    assert "mask_references" in params
    assert "palette" in params

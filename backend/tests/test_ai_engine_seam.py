"""RED/GREEN tests for P8 AI engine seam integration (S3, S6).

Verifies that real adapters implement their Protocols, that ModelUnavailableError
is raised when the model is not available (no silent failure), and that mock
adapters still work as fallback.
"""

import pytest
from app.ai_engine.adapters.real import (
    ModelUnavailableError,
    RealCharacterDetector,
    RealCharacterMatcher,
    RealColorizationEngine,
    RealPanelDetector,
    RealSegmenter,
)
from app.ai_engine.contracts import (
    CharacterDetector,
    CharacterMatcher,
    ColorizationEngine,
    PanelDetector,
    Segmenter,
)


def test_real_adapters_implement_protocols():
    """Todos los adaptadores reales deben pasar isinstance contra su Protocolo."""
    assert isinstance(RealPanelDetector(), PanelDetector)
    assert isinstance(RealCharacterDetector(), CharacterDetector)
    assert isinstance(RealSegmenter(), Segmenter)
    assert isinstance(RealCharacterMatcher(), CharacterMatcher)
    assert isinstance(RealColorizationEngine(), ColorizationEngine)


def test_model_unavailable_error_is_clear():
    """ModelUnavailableError debe tener un mensaje claro con nombre del modelo."""
    err = ModelUnavailableError("panel-detector", "weights not found")
    msg = str(err)
    assert "panel-detector" in msg
    assert "weights not found" in msg


def test_real_adapter_raises_when_model_not_available():
    """Llamar a detect/segment/match/colorize sin modelo cargado debe lanzar
    ModelUnavailableError, no fallar silenciosamente."""
    detector = RealPanelDetector()
    with pytest.raises(ModelUnavailableError):
        detector.detect("fake_page.png")

    matcher = RealCharacterMatcher()
    with pytest.raises(ModelUnavailableError):
        matcher.match([])

    segmenter = RealSegmenter()
    with pytest.raises(ModelUnavailableError):
        segmenter.segment("fake_page.png", regions=[])

    engine = RealColorizationEngine()
    with pytest.raises(ModelUnavailableError):
        engine.colorize(
            image_path="fake_page.png",
            mask_references=[],
            palette={},
        )


def test_mock_adapter_still_works_as_fallback():
    """Los adaptadores mock de P4 siguen funcionando como fallback."""
    from app.ai_engine.adapters.mock.panel_detector import MockPanelDetector

    adapter = MockPanelDetector()
    assert isinstance(adapter, PanelDetector)
    result = adapter.detect("fake_page.png")
    assert isinstance(result, list)
    assert len(result) > 0

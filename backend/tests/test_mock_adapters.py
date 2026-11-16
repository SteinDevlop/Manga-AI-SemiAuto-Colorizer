"""RED/GREEN tests for P4 mock adapters (S2, S3, S5, S6).

Verifies that mock adapters implement their Protocols and return
JSON-serializable dicts with the expected keys.
"""

from app.ai_engine.adapters.mock.character_detector import MockCharacterDetector
from app.ai_engine.adapters.mock.character_matcher import MockCharacterMatcher
from app.ai_engine.adapters.mock.panel_detector import MockPanelDetector
from app.ai_engine.adapters.mock.segmenter import MockSegmenter
from app.ai_engine.contracts import (
    CharacterDetector,
    CharacterMatcher,
    PanelDetector,
    Segmenter,
)


def test_mock_panel_detector_implements_protocol():
    """MockPanelDetector debe pasar isinstance contra PanelDetector."""
    adapter = MockPanelDetector()
    assert isinstance(adapter, PanelDetector)


def test_mock_panel_detector_output():
    """MockPanelDetector debe retornar lista de paneles con claves esperadas."""
    adapter = MockPanelDetector()
    result = adapter.detect("fake_page.png")
    assert isinstance(result, list)
    assert len(result) > 0
    panel = result[0]
    for key in ("numero_orden", "x", "y", "ancho", "alto", "confianza"):
        assert key in panel


def test_mock_character_detector_implements_protocol():
    """MockCharacterDetector debe pasar isinstance contra CharacterDetector."""
    adapter = MockCharacterDetector()
    assert isinstance(adapter, CharacterDetector)


def test_mock_character_detector_output():
    """MockCharacterDetector debe retornar lista de apariciones con claves esperadas."""
    adapter = MockCharacterDetector()
    result = adapter.detect("fake_page.png")
    assert isinstance(result, list)
    assert len(result) > 0
    appearance = result[0]
    for key in ("x", "y", "ancho", "alto", "confianza", "etiqueta"):
        assert key in appearance


def test_mock_segmenter_implements_protocol():
    """MockSegmenter debe pasar isinstance contra Segmenter."""
    adapter = MockSegmenter()
    assert isinstance(adapter, Segmenter)


def test_mock_segmenter_output():
    """MockSegmenter debe retornar máscaras con claves esperadas."""
    adapter = MockSegmenter()
    result = adapter.segment("fake_page.png", regions=[{"region_id": "r1"}])
    assert isinstance(result, list)
    assert len(result) > 0
    mask = result[0]
    for key in ("region_id", "ruta_archivo", "hash_sha256", "ancho", "alto", "tipo_mascara"):
        assert key in mask


def test_mock_character_matcher_implements_protocol():
    """MockCharacterMatcher debe pasar isinstance contra CharacterMatcher."""
    adapter = MockCharacterMatcher()
    assert isinstance(adapter, CharacterMatcher)


def test_mock_character_matcher_output():
    """MockCharacterMatcher debe retornar agrupaciones con claves esperadas."""
    adapter = MockCharacterMatcher()
    result = adapter.match([{"id": "a1"}, {"id": "a2"}])
    assert isinstance(result, list)
    assert len(result) > 0
    proposal = result[0]
    for key in ("apariciones", "confianza_identidad", "nombre_sugerido"):
        assert key in proposal

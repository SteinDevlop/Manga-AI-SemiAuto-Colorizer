"""RED/GREEN tests for P4 AnalyzePageUseCase (S2, S3, S5).

Verifies structure, DTOs, and protocol dependencies without executing
the full orchestration (requires many repository stubs).
"""

import asyncio
import inspect
import uuid
from dataclasses import FrozenInstanceError, dataclass

import pytest
from app.ai_engine.contracts import CharacterDetector, PanelDetector, Segmenter
from app.application.use_cases.analyze_page import (
    AnalyzePageInput,
    AnalyzePageOutput,
    AnalyzePageUseCase,
    CharacterOutput,
    MaskArtifactOutput,
    PanelOutput,
)
from app.core.exceptions import NotFoundError


@dataclass
class StubPage:
    id: uuid.UUID
    ruta_archivo: str


class StubPageRepository:
    def __init__(self, page: StubPage | None):
        self._page = page

    async def get_by_id(self, *, page_id: uuid.UUID):
        return self._page

    async def get(self, *, page_id: uuid.UUID):
        return self._page


class StubDetector:
    """Stub implementing the runtime_checkable Protocol signatures."""

    async def detect(self, image_path: str, *, min_confidence: float = 0.0) -> list[dict]:
        return []


class StubSegmenter:
    async def segment(self, image_path: str, *, regions: list[dict]) -> list[dict]:
        return []


def test_dto_are_frozen():
    """DTOs must be frozen dataclasses (immutable)."""
    panel = PanelOutput(
        id="p1",
        page_id="pg1",
        numero_orden=1,
        x=0.0,
        y=0.0,
        ancho=10.0,
        alto=10.0,
        confianza_deteccion=0.9,
    )
    with pytest.raises(FrozenInstanceError):
        panel.numero_orden = 2


def test_use_case_has_expected_constructor_params():
    """AnalyzePageUseCase must accept the 10 protocol ports keyword-only."""
    sig = inspect.signature(AnalyzePageUseCase.__init__)
    params = list(sig.parameters.keys())
    expected = [
        "self",
        "page_repository",
        "panel_repository",
        "character_repository",
        "character_appearance_repository",
        "analysis_repository",
        "mask_artifact_repository",
        "storage_service",
        "panel_detector",
        "character_detector",
        "segmenter",
    ]
    assert params == expected
    for name in expected[1:]:
        assert sig.parameters[name].kind == inspect.Parameter.KEYWORD_ONLY


def test_detectors_implement_protocols():
    """Detector/segmenter stubs must be Protocol instances at runtime."""
    assert isinstance(StubDetector(), PanelDetector)
    assert isinstance(StubDetector(), CharacterDetector)
    assert isinstance(StubSegmenter(), Segmenter)


def test_execute_raises_notfound_when_page_missing():
    """execute must raise NotFoundError when page does not exist."""
    use_case = AnalyzePageUseCase(
        page_repository=StubPageRepository(None),
        panel_repository=StubDetector(),
        character_repository=StubDetector(),
        character_appearance_repository=StubDetector(),
        analysis_repository=StubDetector(),
        mask_artifact_repository=StubDetector(),
        storage_service=StubDetector(),
        panel_detector=StubDetector(),
        character_detector=StubDetector(),
        segmenter=StubSegmenter(),
    )
    with pytest.raises(NotFoundError):
        asyncio.run(use_case.execute(AnalyzePageInput(page_id=uuid.uuid4())))


def test_output_dto_fields():
    """AnalyzePageOutput must have all expected fields."""
    output = AnalyzePageOutput(
        analysis_id="a1",
        page_id="p1",
        estado="analysis_completed",
        confianza_global=0.0,
        version_modelo="mock-v1",
        panels=[],
        characters=[],
        appearances=[],
        masks=[],
    )
    assert output.analysis_id == "a1"
    assert output.page_id == "p1"
    assert output.estado == "analysis_completed"
    assert output.panels == []
    assert output.masks == []


def test_panel_output_fields():
    """PanelOutput must have expected fields."""
    panel = PanelOutput(
        id="p1",
        page_id="pg1",
        numero_orden=1,
        x=0.0,
        y=0.0,
        ancho=10.0,
        alto=10.0,
        confianza_deteccion=0.9,
    )
    assert panel.numero_orden == 1
    assert panel.x == 0.0
    assert panel.confianza_deteccion == 0.9


def test_character_output_fields():
    """CharacterOutput must have expected fields."""
    char = CharacterOutput(id="c1", nombre="Protagonista", confianza_identidad=0.9)
    assert char.nombre == "Protagonista"
    assert char.confianza_identidad == 0.9


def test_mask_artifact_output_fields():
    """MaskArtifactOutput must have expected fields."""
    mask = MaskArtifactOutput(
        id="m1",
        appearance_id="a1",
        tipo_mascara="character",
        ruta_archivo="/data/masks/m1.png",
        hash_sha256="abc123",
        ancho=100,
        alto=100,
    )
    assert mask.tipo_mascara == "character"
    assert mask.hash_sha256 == "abc123"

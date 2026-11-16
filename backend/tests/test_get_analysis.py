"""RED/GREEN tests for P4 GetAnalysisUseCase (read path).

Verifies structure, DTOs, and protocol dependencies.
"""

import asyncio
import inspect
import uuid
from dataclasses import FrozenInstanceError, dataclass

import pytest

from app.application.use_cases.get_analysis import (
    GetAnalysisInput,
    GetAnalysisOutput,
    GetAnalysisUseCase,
    MaskArtifactOutput,
)
from app.core.exceptions import NotFoundError


class StubProtocol:
    """Minimal stub for repository ports."""

    async def get(self, *, analysis_id=None, appearance_id=None, character_id=None):
        return None

    async def list(self, *, page_id=None, character_id=None, appearance_id=None):
        return []

    async def list_by_page(self, *, page_id=None):
        return []

    async def create(self, **kwargs):
        return None

    async def update(self, **kwargs):
        return None

    async def update_character(self, *, appearance_id=None, character_id=None):
        return None

    async def exists(self, **kwargs):
        return False

    async def exists_by_name(self, **kwargs):
        return False

    async def exists_by_page_id(self, **kwargs):
        return False

    async def exists_by_hash(self, **kwargs):
        return False

    async def get_by_id(self, **kwargs):
        return None

    async def get_by_page_id(self, **kwargs):
        return None


def test_dto_are_frozen():
    """DTOs must be frozen dataclasses (immutable)."""
    mask = MaskArtifactOutput(
        id="m1",
        appearance_id="a1",
        tipo_mascara="character",
        ruta_archivo="/data/masks/m1.png",
        hash_sha256="abc123",
        ancho=100,
        alto=100,
    )
    with pytest.raises(FrozenInstanceError):
        mask.tipo_mascara = "other"


def test_use_case_has_expected_constructor_params():
    """GetAnalysisUseCase must accept the 5 repository ports keyword-only."""
    sig = inspect.signature(GetAnalysisUseCase.__init__)
    params = list(sig.parameters.keys())
    expected = [
        "self",
        "analysis_repository",
        "panel_repository",
        "character_repository",
        "character_appearance_repository",
        "mask_artifact_repository",
    ]
    assert params == expected
    for name in expected[1:]:
        assert sig.parameters[name].kind == inspect.Parameter.KEYWORD_ONLY


def test_execute_raises_notfound_when_analysis_missing():
    """execute must raise NotFoundError when analysis does not exist."""
    use_case = GetAnalysisUseCase(
        analysis_repository=StubProtocol(),
        panel_repository=StubProtocol(),
        character_repository=StubProtocol(),
        character_appearance_repository=StubProtocol(),
        mask_artifact_repository=StubProtocol(),
    )
    with pytest.raises(NotFoundError):
        asyncio.run(
            use_case.execute(GetAnalysisInput(analysis_id=uuid.uuid4()))
        )


def test_output_dto_fields():
    """GetAnalysisOutput must have all expected fields."""
    output = GetAnalysisOutput(
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
    assert output.masks == []

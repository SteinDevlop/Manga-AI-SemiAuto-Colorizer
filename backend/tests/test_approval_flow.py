"""RED/GREEN tests for P6 approval flow (S4, S5, S9).

Verifies ApproveAnalysisUseCase and CreateColorizationJobUseCase with
stub protocol repositories (no database required).
"""

import asyncio
import uuid
from dataclasses import FrozenInstanceError, dataclass
from typing import Any

import pytest
from app.application.use_cases.approve_analysis import (
    ApproveAnalysisInput,
    ApproveAnalysisUseCase,
)
from app.application.use_cases.create_colorization_job import (
    CreateColorizationJobInput,
    CreateColorizationJobUseCase,
)
from app.core.exceptions import NotFoundError, ValidationError


@dataclass
class StubAnalysis:
    id: uuid.UUID
    analysis_id: uuid.UUID
    estado: str = "REVIEW_REQUIRED"


@dataclass
class StubJob:
    id: uuid.UUID
    analysis_id: uuid.UUID
    estado: str = "pending"
    progreso: int = 0


class StubAnalysisRepository:
    def __init__(self, analyses: list[StubAnalysis]):
        self._analyses = {a.id: a for a in analyses}
        self.updated: dict[uuid.UUID, str] = {}

    async def get(self, *, analysis_id: uuid.UUID) -> StubAnalysis | None:
        return self._analyses.get(analysis_id)

    async def update(
        self,
        *,
        analysis_id: uuid.UUID,
        estado: str | None = None,
    ) -> StubAnalysis | None:
        analysis = self._analyses.get(analysis_id)
        if analysis is None:
            return None
        if estado is not None:
            analysis.estado = estado
        self.updated[analysis_id] = analysis.estado
        return analysis


class StubColorizationJobRepository:
    def __init__(self):
        self.created: list[dict[str, Any]] = []

    async def create(self, **kwargs: Any) -> StubJob:
        job = StubJob(
            id=uuid.uuid4(),
            analysis_id=kwargs["analysis_id"],
            estado=kwargs.get("estado", "pending"),
            progreso=kwargs.get("progreso", 0),
        )
        self.created.append(
            {
                "analysis_id": kwargs["analysis_id"],
                "estado": kwargs.get("estado"),
                "progreso": kwargs.get("progreso"),
            }
        )
        return job


def test_dtos_are_frozen():
    """DTOs must be frozen dataclasses (immutable)."""
    inp = ApproveAnalysisInput(analysis_id=uuid.uuid4())
    with pytest.raises(FrozenInstanceError):
        inp.analysis_id = uuid.uuid4()


def test_approve_analysis_happy_path():
    """Debe marcar el análisis como APPROVED."""
    analysis_id = uuid.uuid4()
    analysis = StubAnalysis(id=analysis_id, analysis_id=analysis_id, estado="REVIEW_REQUIRED")
    repo = StubAnalysisRepository([analysis])
    use_case = ApproveAnalysisUseCase(analysis_repository=repo)
    output = asyncio.run(use_case.execute(ApproveAnalysisInput(analysis_id=analysis_id)))

    assert output.estado == "APPROVED"
    assert repo.updated[analysis_id] == "APPROVED"


def test_approve_analysis_not_found():
    """Debe lanzar NotFoundError si el análisis no existe."""
    use_case = ApproveAnalysisUseCase(analysis_repository=StubAnalysisRepository([]))
    with pytest.raises(NotFoundError):
        asyncio.run(
            use_case.execute(ApproveAnalysisInput(analysis_id=uuid.uuid4()))
        )


def test_create_colorization_job_blocked_without_approval():
    """Debe lanzar ValidationError si el análisis no está APPROVED."""
    analysis_id = uuid.uuid4()
    analysis = StubAnalysis(id=analysis_id, analysis_id=analysis_id, estado="REVIEW_REQUIRED")
    analysis_repo = StubAnalysisRepository([analysis])
    job_repo = StubColorizationJobRepository()
    use_case = CreateColorizationJobUseCase(
        analysis_repository=analysis_repo,
        colorization_job_repository=job_repo,
    )
    with pytest.raises(ValidationError):
        asyncio.run(
            use_case.execute(
                CreateColorizationJobInput(analysis_id=analysis_id)
            )
        )


def test_create_colorization_job_happy_path():
    """Debe crear el job solo si el análisis está APPROVED."""
    analysis_id = uuid.uuid4()
    analysis = StubAnalysis(id=analysis_id, analysis_id=analysis_id, estado="APPROVED")
    analysis_repo = StubAnalysisRepository([analysis])
    job_repo = StubColorizationJobRepository()
    use_case = CreateColorizationJobUseCase(
        analysis_repository=analysis_repo,
        colorization_job_repository=job_repo,
    )
    output = asyncio.run(
        use_case.execute(
            CreateColorizationJobInput(analysis_id=analysis_id)
        )
    )

    assert output.estado == "pending"
    assert output.progreso == 0
    assert len(job_repo.created) == 1


def test_create_colorization_job_not_found():
    """Debe lanzar NotFoundError si el análisis no existe."""
    use_case = CreateColorizationJobUseCase(
        analysis_repository=StubAnalysisRepository([]),
        colorization_job_repository=StubColorizationJobRepository(),
    )
    with pytest.raises(NotFoundError):
        asyncio.run(
            use_case.execute(
                CreateColorizationJobInput(analysis_id=uuid.uuid4())
            )
        )

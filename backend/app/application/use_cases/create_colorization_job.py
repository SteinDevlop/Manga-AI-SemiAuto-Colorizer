"""Create colorization job use case.

Creates a ColorizationJob only when the source analysis has been APPROVED.
Blocks colorization when required analysis/configuration is not approved
(ADR-005, README rule 9).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from app.core.exceptions import NotFoundError, ValidationError


class AnalysisRepository(Protocol):
    """Port for analysis read operations."""

    async def get(self, *, analysis_id: UUID) -> Any | None:  # pragma: no cover - protocol stub
        """Return the analysis with the given ID, or None when not found."""
        ...


class ColorizationJobRepository(Protocol):
    """Port for colorization job write operations."""

    async def create(self, **kwargs: Any) -> Any:  # pragma: no cover - protocol stub
        """Create and persist a colorization job, returning the entity."""
        ...


@dataclass(frozen=True)
class CreateColorizationJobInput:
    """Input data for creating a colorization job."""

    analysis_id: UUID


@dataclass(frozen=True)
class CreateColorizationJobOutput:
    """Simple output DTO for a created colorization job, never an ORM model."""

    job_id: str
    analysis_id: str
    estado: str
    progreso: int


class CreateColorizationJobUseCase:
    """Create a colorization job only when the analysis is approved."""

    def __init__(
        self,
        analysis_repository: AnalysisRepository,
        colorization_job_repository: ColorizationJobRepository,
    ) -> None:
        self._analysis_repository = analysis_repository
        self._colorization_job_repository = colorization_job_repository

    async def execute(
        self, input_data: CreateColorizationJobInput
    ) -> CreateColorizationJobOutput:
        """Execute the create colorization job use case.

        Raises:
            NotFoundError: when no analysis matches the given ID.
            ValidationError: when the analysis is not APPROVED.
        """
        analysis = await self._analysis_repository.get(
            analysis_id=input_data.analysis_id
        )
        if analysis is None:
            raise NotFoundError(
                message="Analysis not found.",
                details={"field": "analysis_id", "reason": "not_found"},
            )

        if str(getattr(analysis, "estado", "")).upper() != "APPROVED":
            raise ValidationError(
                message=(
                    "Cannot create colorization job: analysis is not approved. "
                    "Approve identities, attributes and palettes first."
                ),
                details={
                    "field": "analysis_id",
                    "reason": "analysis_not_approved",
                    "current_state": str(getattr(analysis, "estado", None)),
                },
            )

        job = await self._colorization_job_repository.create(
            analysis_id=input_data.analysis_id,
            estado="pending",
            progreso=0,
        )

        return CreateColorizationJobOutput(
            job_id=str(job.id),
            analysis_id=str(input_data.analysis_id),
            estado=str(getattr(job, "estado", "pending")),
            progreso=int(getattr(job, "progreso", 0)),
        )

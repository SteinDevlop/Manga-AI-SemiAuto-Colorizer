"""Approve analysis use case.

Marks a page analysis as APPROVED after the user has reviewed identities,
attributes and palettes. Human-in-the-loop: no colorization job can be
created without a valid approval (ADR-005).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger

logger = get_logger(__name__)


class AnalysisRepository(Protocol):
    """Port for analysis read/write operations."""

    async def get(self, *, analysis_id: UUID) -> Any | None:  # pragma: no cover - protocol stub
        """Return the analysis with the given ID, or None when not found."""
        ...

    async def update(
        self,
        *,
        analysis_id: UUID,
        estado: str | None = None,
    ) -> Any | None:  # pragma: no cover - protocol stub
        """Update analysis state, returning the persisted entity or None."""
        ...


@dataclass(frozen=True)
class ApproveAnalysisInput:
    """Input data for approving an analysis."""

    analysis_id: UUID


@dataclass(frozen=True)
class ApproveAnalysisOutput:
    """Simple output DTO for an approved analysis, never an ORM model."""

    analysis_id: str
    estado: str


class ApproveAnalysisUseCase:
    """Approve a page analysis so a colorization job can be created."""

    def __init__(
        self,
        analysis_repository: AnalysisRepository,
    ) -> None:
        self._analysis_repository = analysis_repository

    async def execute(self, input_data: ApproveAnalysisInput) -> ApproveAnalysisOutput:
        """Execute the approve analysis use case.

        Raises:
            NotFoundError: when no analysis matches the given ID.
        """
        try:
            analysis = await self._analysis_repository.get(analysis_id=input_data.analysis_id)
            if analysis is None:
                logger.warning("Análisis no encontrado para aprobación: %s", input_data.analysis_id)
                raise NotFoundError(
                    message="Analysis not found.",
                    details={"field": "analysis_id", "reason": "not_found"},
                )

            updated = await self._analysis_repository.update(
                analysis_id=input_data.analysis_id,
                estado="APPROVED",
            )
            if updated is None:
                raise NotFoundError(
                    message="Analysis not found.",
                    details={"field": "analysis_id", "reason": "not_found"},
                )

            logger.info(
                "Análisis aprobado: %s (estado: APPROVED)", input_data.analysis_id
            )
            return ApproveAnalysisOutput(
                analysis_id=str(updated.id),
                estado=str(updated.estado),
            )
        except NotFoundError:
            raise
        except Exception as exc:  # pragma: no cover - infra failure path
            logger.exception(
                "Error al aprobar análisis %s: %s",
                input_data.analysis_id,
                exc,
            )
            raise

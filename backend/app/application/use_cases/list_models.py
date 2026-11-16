"""List models use case.

Returns all registered model manifests with their capabilities and status.
Depends on the model manifest repository port, never on concrete ORM models
or AI models.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID


class ModelManifestEntity(Protocol):
    """Structural protocol for a model manifest entity (never an ORM class)."""

    id: UUID
    nombre_modelo: str
    familia: str
    version: str
    hash_pesos: str | None
    licencia: str | None
    fuente: str | None
    capacidades: dict[str, Any] | None
    requisitos_hardware: dict[str, Any] | None
    estado: str
    created_at: datetime
    updated_at: datetime


class ModelManifestRepository(Protocol):
    """Port for model manifest persistence operations."""

    async def list(  # pragma: no cover - protocol stub
        self,
    ) -> list[ModelManifestEntity]:
        """Return all registered model manifests ordered by creation time."""
        ...


@dataclass(frozen=True)
class ListModelsInput:
    """Input data for listing models."""


@dataclass(frozen=True)
class ModelManifestOutput:
    """Simple output DTO for a model manifest, never an ORM model."""

    id: str
    nombre_modelo: str
    familia: str
    version: str
    hash_pesos: str | None
    licencia: str | None
    fuente: str | None
    capacidades: dict[str, Any] | None
    requisitos_hardware: dict[str, Any] | None
    estado: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class ListModelsOutput:
    """List of model manifests."""

    items: list[ModelManifestOutput]


class ListModelsUseCase:
    """List all registered model manifests."""

    def __init__(self, model_manifest_repository: ModelManifestRepository) -> None:
        self._model_manifest_repository = model_manifest_repository

    async def execute(self, input_data: ListModelsInput) -> ListModelsOutput:
        """Execute the list models use case."""
        entities = await self._model_manifest_repository.list()

        return ListModelsOutput(
            items=[
                ModelManifestOutput(
                    id=str(entity.id),
                    nombre_modelo=entity.nombre_modelo,
                    familia=entity.familia,
                    version=entity.version,
                    hash_pesos=entity.hash_pesos,
                    licencia=entity.licencia,
                    fuente=entity.fuente,
                    capacidades=entity.capacidades,
                    requisitos_hardware=entity.requisitos_hardware,
                    estado=entity.estado,
                    created_at=entity.created_at.isoformat(),
                    updated_at=entity.updated_at.isoformat(),
                )
                for entity in entities
            ],
        )

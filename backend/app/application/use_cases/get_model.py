"""Get model use case.

Returns a model manifest by its ID or raises NotFoundError when missing.
Depends on the model manifest repository port, never on concrete ORM models
or AI models.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from app.core.exceptions import NotFoundError


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

    async def get(  # pragma: no cover - protocol stub
        self, *, manifest_id: UUID
    ) -> ModelManifestEntity | None:
        """Return the manifest with the given id, or None when not found."""
        ...


@dataclass(frozen=True)
class GetModelInput:
    """Input data for getting a model."""

    model_id: UUID


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


class GetModelUseCase:
    """Retrieve a model manifest by ID."""

    def __init__(self, model_manifest_repository: ModelManifestRepository) -> None:
        self._model_manifest_repository = model_manifest_repository

    async def execute(self, input_data: GetModelInput) -> ModelManifestOutput:
        """Execute the get model use case.

        Raises:
            NotFoundError: when no manifest matches the given model ID.
        """
        entity = await self._model_manifest_repository.get(manifest_id=input_data.model_id)
        if entity is None:
            raise NotFoundError(
                message="Model not found.",
                details={"field": "model_id", "reason": "not_found"},
            )

        return ModelManifestOutput(
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

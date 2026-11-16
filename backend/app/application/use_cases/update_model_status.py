"""Update model status use case.

Updates the status of a model manifest to one of the allowed values:
disponible, experimental or deshabilitado. Depends on the model manifest
repository port, never on concrete ORM models or AI models.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from app.core.exceptions import NotFoundError, ValidationError


VALID_MODEL_STATES = frozenset({"disponible", "experimental", "deshabilitado"})


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

    async def update(  # pragma: no cover - protocol stub
        self, *, manifest_id: UUID, **kwargs: Any
    ) -> ModelManifestEntity | None:
        """Update the attributes of the manifest with the given id."""
        ...


@dataclass(frozen=True)
class UpdateModelStatusInput:
    """Input data for updating a model status."""

    model_id: UUID
    estado: str


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


def _require_valid_estado(estado: str) -> None:
    """Raise ValidationError when estado is not an allowed model status."""
    if estado not in VALID_MODEL_STATES:
        raise ValidationError(
            message=f"Invalid model status: {estado!r}.",
            details={
                "field": "estado",
                "reason": "invalid_status",
                "allowed": sorted(VALID_MODEL_STATES),
            },
        )


class UpdateModelStatusUseCase:
    """Update the status of a model manifest."""

    def __init__(self, model_manifest_repository: ModelManifestRepository) -> None:
        self._model_manifest_repository = model_manifest_repository

    async def execute(self, input_data: UpdateModelStatusInput) -> ModelManifestOutput:
        """Execute the update model status use case.

        Raises:
            ValidationError: when the requested status is not allowed.
            NotFoundError: when no manifest matches the given model ID.
        """
        _require_valid_estado(input_data.estado)

        entity = await self._model_manifest_repository.get(
            manifest_id=input_data.model_id
        )
        if entity is None:
            raise NotFoundError(
                message="Model not found.",
                details={"field": "model_id", "reason": "not_found"},
            )

        updated = await self._model_manifest_repository.update(
            manifest_id=input_data.model_id,
            estado=input_data.estado,
        )
        if updated is None:
            raise NotFoundError(
                message="Model not found.",
                details={"field": "model_id", "reason": "not_found"},
            )

        return ModelManifestOutput(
            id=str(updated.id),
            nombre_modelo=updated.nombre_modelo,
            familia=updated.familia,
            version=updated.version,
            hash_pesos=updated.hash_pesos,
            licencia=updated.licencia,
            fuente=updated.fuente,
            capacidades=updated.capacidades,
            requisitos_hardware=updated.requisitos_hardware,
            estado=updated.estado,
            created_at=updated.created_at.isoformat(),
            updated_at=updated.updated_at.isoformat(),
        )

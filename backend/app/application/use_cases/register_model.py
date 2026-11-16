"""Register model use case.

Registers a new model manifest, ensuring no duplicate combination of name,
family and version already exists. Depends on the model manifest repository
port, never on concrete ORM models or AI models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from app.core.exceptions import ConflictError


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

    async def create(  # pragma: no cover - protocol stub
        self, **kwargs: Any
    ) -> ModelManifestEntity:
        """Create and persist a model manifest, returning the persisted entity."""
        ...


@dataclass(frozen=True)
class RegisterModelInput:
    """Input data for registering a model manifest."""

    nombre: str
    familia: str
    version: str
    estado: str = "disponible"
    hash_pesos: str | None = None
    licencia: str | None = None
    fuente: str | None = None
    capacidades: dict[str, Any] = field(default_factory=dict)
    requisitos_hardware: dict[str, Any] = field(default_factory=dict)


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


class RegisterModelUseCase:
    """Register a new model manifest ensuring name+family+version uniqueness."""

    def __init__(self, model_manifest_repository: ModelManifestRepository) -> None:
        self._model_manifest_repository = model_manifest_repository

    async def execute(self, input_data: RegisterModelInput) -> ModelManifestOutput:
        """Execute the register model use case.

        Raises:
            ConflictError: when a model with the same name, family and version
                is already registered.
        """
        await self._ensure_no_duplicate(input_data)

        entity = await self._model_manifest_repository.create(
            nombre_modelo=input_data.nombre,
            familia=input_data.familia,
            version=input_data.version,
            hash_pesos=input_data.hash_pesos,
            licencia=input_data.licencia,
            fuente=input_data.fuente,
            capacidades=input_data.capacidades,
            requisitos_hardware=input_data.requisitos_hardware,
            estado=input_data.estado,
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

    async def _ensure_no_duplicate(self, input_data: RegisterModelInput) -> None:
        """Raise ConflictError when a manifest with same name+family+version exists."""
        entities = await self._model_manifest_repository.list()
        for entity in entities:
            if (
                entity.nombre_modelo == input_data.nombre
                and entity.familia == input_data.familia
                and entity.version == input_data.version
            ):
                raise ConflictError(
                    message="A model with this name, family and version already exists.",
                    details={
                        "field": "nombre,familia,version",
                        "reason": "duplicate_model",
                    },
                )

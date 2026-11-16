"""RED/GREEN tests for P8 model registry use cases (S2, S7).

Verifies RegisterModelUseCase, ListModelsUseCase, UpdateModelStatusUseCase,
GetModelUseCase with stub protocol repositories (no database required).
"""

import asyncio
import uuid
from dataclasses import FrozenInstanceError, dataclass, field
from datetime import datetime, timezone
from typing import Any

import pytest
from app.application.use_cases.get_model import GetModelInput, GetModelUseCase
from app.application.use_cases.list_models import ListModelsInput, ListModelsUseCase
from app.application.use_cases.register_model import (
    RegisterModelInput,
    RegisterModelUseCase,
)
from app.application.use_cases.update_model_status import (
    UpdateModelStatusInput,
    UpdateModelStatusUseCase,
)
from app.core.exceptions import ConflictError, NotFoundError, ValidationError


@dataclass
class StubModelManifest:
    id: uuid.UUID
    nombre_modelo: str
    familia: str
    version: str
    hash_pesos: str | None = None
    licencia: str | None = None
    fuente: str | None = None
    capacidades: dict[str, Any] | None = None
    requisitos_hardware: dict[str, Any] | None = None
    estado: str = "disponible"
    parametros_soportados: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class StubModelManifestRepository:
    def __init__(self, manifests: list[StubModelManifest]):
        self._manifests = {m.id: m for m in manifests}
        self.created: list[StubModelManifest] = []
        self.updated: dict[uuid.UUID, dict[str, Any]] = {}

    async def get(self, *, manifest_id: uuid.UUID) -> StubModelManifest | None:
        return self._manifests.get(manifest_id)

    async def list(self) -> list[StubModelManifest]:
        return list(self._manifests.values())

    async def create(self, **kwargs: Any) -> StubModelManifest:
        mid = kwargs.get("id", uuid.uuid4())
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        manifest = StubModelManifest(
            id=mid,
            nombre_modelo=kwargs["nombre_modelo"],
            familia=kwargs["familia"],
            version=kwargs["version"],
            hash_pesos=kwargs.get("hash_pesos"),
            licencia=kwargs.get("licencia"),
            fuente=kwargs.get("fuente"),
            capacidades=kwargs.get("capacidades"),
            requisitos_hardware=kwargs.get("requisitos_hardware"),
            estado=kwargs.get("estado", "disponible"),
            parametros_soportados=kwargs.get("parametros_soportados"),
            created_at=now,
            updated_at=now,
        )
        self._manifests[mid] = manifest
        self.created.append(manifest)
        return manifest

    async def update(
        self,
        manifest_id: uuid.UUID,
        **kwargs: Any,
    ) -> StubModelManifest | None:
        manifest = self._manifests.get(manifest_id)
        if manifest is None:
            return None
        for key, value in kwargs.items():
            setattr(manifest, key, value)
        self.updated[manifest_id] = {
            "estado": manifest.estado,
        }
        return manifest

    async def delete(self, manifest_id: uuid.UUID) -> bool:
        if manifest_id not in self._manifests:
            return False
        del self._manifests[manifest_id]
        return True

    async def exists(self, manifest_id: uuid.UUID) -> bool:
        return manifest_id in self._manifests


def test_dto_are_frozen():
    """DTOs must be frozen dataclasses (immutable)."""
    inp = RegisterModelInput(
        nombre="test-model",
        familia="test-family",
        version="1.0.0",
    )
    with pytest.raises(FrozenInstanceError):
        inp.version = "2.0.0"


def test_register_model_happy_path():
    """Debe registrar un modelo nuevo."""
    repo = StubModelManifestRepository([])
    use_case = RegisterModelUseCase(model_manifest_repository=repo)
    output = asyncio.run(
        use_case.execute(
            RegisterModelInput(
                nombre="manga-colorizer",
                familia="stable-diffusion",
                version="1.0.0",
                hash_pesos="abc123",
                licencia="mit",
                fuente="local",
                capacidades={"deteccion": True, "segmentacion": True},
                requisitos_hardware={"vram_gb": 8},
                estado="disponible",
            )
        )
    )

    assert output.nombre_modelo == "manga-colorizer"
    assert output.familia == "stable-diffusion"
    assert output.version == "1.0.0"
    assert output.estado == "disponible"
    assert len(repo.created) == 1


def test_register_model_duplicate_rejects():
    """Registro duplicado (mismo nombre+familia+versión) debe lanzar ConflictError."""
    mid = uuid.uuid4()
    existing = StubModelManifest(
        id=mid,
        nombre_modelo="manga-colorizer",
        familia="stable-diffusion",
        version="1.0.0",
    )
    repo = StubModelManifestRepository([existing])
    use_case = RegisterModelUseCase(model_manifest_repository=repo)
    with pytest.raises(ConflictError):
        asyncio.run(
            use_case.execute(
                RegisterModelInput(
                    nombre="manga-colorizer",
                    familia="stable-diffusion",
                    version="1.0.0",
                )
            )
        )


def test_list_models():
    """Debe listar todos los modelos registrados."""
    mid1 = uuid.uuid4()
    mid2 = uuid.uuid4()
    repo = StubModelManifestRepository(
        [
            StubModelManifest(id=mid1, nombre_modelo="model-a", familia="f1", version="1.0"),
            StubModelManifest(id=mid2, nombre_modelo="model-b", familia="f2", version="2.0"),
        ]
    )
    use_case = ListModelsUseCase(model_manifest_repository=repo)
    output = asyncio.run(use_case.execute(ListModelsInput()))

    assert len(output.items) == 2


def test_get_model_happy_path():
    """Debe retornar el modelo existente."""
    mid = uuid.uuid4()
    manifest = StubModelManifest(id=mid, nombre_modelo="m", familia="f", version="1.0")
    repo = StubModelManifestRepository([manifest])
    use_case = GetModelUseCase(model_manifest_repository=repo)
    output = asyncio.run(use_case.execute(GetModelInput(model_id=mid)))

    assert output.id == str(mid)
    assert output.nombre_modelo == "m"


def test_get_model_not_found():
    """Debe lanzar NotFoundError si el modelo no existe."""
    use_case = GetModelUseCase(model_manifest_repository=StubModelManifestRepository([]))
    with pytest.raises(NotFoundError):
        asyncio.run(use_case.execute(GetModelInput(model_id=uuid.uuid4())))


def test_update_model_status_valid():
    """Debe actualizar el estado a un valor válido."""
    mid = uuid.uuid4()
    manifest = StubModelManifest(
        id=mid, nombre_modelo="m", familia="f", version="1.0", estado="disponible"
    )
    repo = StubModelManifestRepository([manifest])
    use_case = UpdateModelStatusUseCase(model_manifest_repository=repo)
    output = asyncio.run(
        use_case.execute(UpdateModelStatusInput(model_id=mid, estado="experimental"))
    )

    assert output.estado == "experimental"
    assert repo.updated[mid]["estado"] == "experimental"


def test_update_model_status_invalid_rejects():
    """Estado inválido debe lanzar ValidationError."""
    mid = uuid.uuid4()
    manifest = StubModelManifest(id=mid, nombre_modelo="m", familia="f", version="1.0")
    repo = StubModelManifestRepository([manifest])
    use_case = UpdateModelStatusUseCase(model_manifest_repository=repo)
    with pytest.raises(ValidationError):
        asyncio.run(
            use_case.execute(UpdateModelStatusInput(model_id=mid, estado="estado-inexistente"))
        )


def test_update_model_status_not_found():
    """Modelo inexistente debe lanzar NotFoundError."""
    use_case = UpdateModelStatusUseCase(model_manifest_repository=StubModelManifestRepository([]))
    with pytest.raises(NotFoundError):
        asyncio.run(
            use_case.execute(UpdateModelStatusInput(model_id=uuid.uuid4(), estado="disponible"))
        )

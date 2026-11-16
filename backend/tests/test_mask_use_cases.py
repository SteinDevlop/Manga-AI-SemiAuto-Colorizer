"""RED/GREEN tests for P6 mask use cases (S3).

Verifies edit/replace/correct mask use cases with stub protocol
repositories (no database required).
"""

import asyncio
import hashlib
import uuid
from dataclasses import FrozenInstanceError, dataclass
from typing import Any

import pytest
from app.application.use_cases.correct_mask import (
    CorrectMaskInput,
    CorrectMaskUseCase,
)
from app.application.use_cases.edit_mask import (
    EditMaskInput,
    EditMaskUseCase,
)
from app.application.use_cases.replace_mask import (
    ReplaceMaskInput,
    ReplaceMaskUseCase,
)
from app.core.exceptions import NotFoundError, ValidationError


@dataclass
class StubArtifact:
    id: uuid.UUID
    appearance_id: uuid.UUID
    tipo_mascara: str
    ruta_archivo: str
    hash_sha256: str
    ancho: int | None = None
    alto: int | None = None
    version: int = 1


class StubArtifactRepository:
    def __init__(self, artifacts: list[StubArtifact]):
        self._artifacts = {a.id: a for a in artifacts}
        self._by_appearance: dict[uuid.UUID, list[StubArtifact]] = {}
        for a in artifacts:
            self._by_appearance.setdefault(a.appearance_id, []).append(a)
        self.updated: dict[uuid.UUID, dict[str, Any]] = {}

    async def get_by_appearance_and_type(
        self,
        *,
        appearance_id: uuid.UUID,
        tipo_mascara: str,
    ) -> StubArtifact | None:
        for a in self._by_appearance.get(appearance_id, []):
            if a.tipo_mascara == tipo_mascara:
                return a
        return None

    async def list_by_appearance(
        self,
        *,
        appearance_id: uuid.UUID,
    ) -> list[StubArtifact]:
        return list(self._by_appearance.get(appearance_id, []))

    async def create(self, **kwargs: Any) -> StubArtifact:
        aid = kwargs.get("id", uuid.uuid4())
        artifact = StubArtifact(
            id=aid,
            appearance_id=kwargs["appearance_id"],
            tipo_mascara=kwargs["tipo_mascara"],
            ruta_archivo=kwargs["ruta_archivo"],
            hash_sha256=kwargs["hash_sha256"],
            ancho=kwargs.get("ancho"),
            alto=kwargs.get("alto"),
            version=kwargs.get("version", 1),
        )
        self._artifacts[aid] = artifact
        self._by_appearance.setdefault(artifact.appearance_id, []).append(artifact)
        return artifact

    async def update(
        self,
        artifact_id: uuid.UUID,
        **kwargs: Any,
    ) -> StubArtifact | None:
        artifact = self._artifacts.get(artifact_id)
        if artifact is None:
            return None
        for key, value in kwargs.items():
            setattr(artifact, key, value)
        self.updated[artifact_id] = {
            "version": artifact.version,
            "ruta_archivo": artifact.ruta_archivo,
            "hash_sha256": artifact.hash_sha256,
        }
        return artifact


class StubStorageService:
    def __init__(self, files: dict[str, bytes]):
        self._files = files

    def sha256_of_file(self, path: str) -> str:
        content = self._files.get(path, b"")
        return hashlib.sha256(content).hexdigest()


def test_dtos_are_frozen():
    """DTOs must be frozen dataclasses (immutable)."""
    inp = EditMaskInput(
        appearance_id=uuid.uuid4(),
        tipo_mascara="caracter",
    )
    with pytest.raises(FrozenInstanceError):
        inp.tipo_mascara = "fondo"


def test_edit_mask_creates_new():
    """Debe crear una máscara cuando no existe."""
    appearance_id = uuid.uuid4()
    repo = StubArtifactRepository([])
    storage = StubStorageService({"/data/masks/m1.png": b"mask data"})
    use_case = EditMaskUseCase(
        artifact_repository=repo,
        storage_service=storage,
    )
    output = asyncio.run(
        use_case.execute(
            EditMaskInput(
                appearance_id=appearance_id,
                tipo_mascara="caracter",
                ruta_archivo="/data/masks/m1.png",
            )
        )
    )

    assert output.tipo_mascara == "caracter"
    assert output.version == 1
    assert output.hash_sha256 == storage.sha256_of_file("/data/masks/m1.png")


def test_replace_mask_requires_existing():
    """replace_mask debe lanzar NotFoundError si no existe máscara."""
    appearance_id = uuid.uuid4()
    repo = StubArtifactRepository([])
    storage = StubStorageService({"/data/masks/m2.png": b"new mask"})
    use_case = ReplaceMaskUseCase(
        artifact_repository=repo,
        storage_service=storage,
    )
    with pytest.raises(NotFoundError):
        asyncio.run(
            use_case.execute(
                ReplaceMaskInput(
                    appearance_id=appearance_id,
                    nueva_ruta_archivo="/data/masks/m2.png",
                    nuevo_hash_sha256="abc",
                )
            )
        )


def test_replace_mask_increments_version():
    """replace_mask debe incrementar la versión."""
    appearance_id = uuid.uuid4()
    artifact = StubArtifact(
        id=uuid.uuid4(),
        appearance_id=appearance_id,
        tipo_mascara="caracter",
        ruta_archivo="/data/masks/old.png",
        hash_sha256="oldhash",
        version=1,
    )
    repo = StubArtifactRepository([artifact])
    storage = StubStorageService({"/data/masks/new.png": b"new mask data"})
    use_case = ReplaceMaskUseCase(
        artifact_repository=repo,
        storage_service=storage,
    )
    output = asyncio.run(
        use_case.execute(
            ReplaceMaskInput(
                appearance_id=appearance_id,
                nueva_ruta_archivo="/data/masks/new.png",
                nuevo_hash_sha256=storage.sha256_of_file("/data/masks/new.png"),
            )
        )
    )

    assert output.version == 2


def test_replace_mask_hash_mismatch():
    """replace_mask debe lanzar ValidationError si el hash no coincide."""
    appearance_id = uuid.uuid4()
    artifact = StubArtifact(
        id=uuid.uuid4(),
        appearance_id=appearance_id,
        tipo_mascara="caracter",
        ruta_archivo="/data/masks/old.png",
        hash_sha256="oldhash",
        version=1,
    )
    repo = StubArtifactRepository([artifact])
    storage = StubStorageService({"/data/masks/new.png": b"new mask data"})
    use_case = ReplaceMaskUseCase(
        artifact_repository=repo,
        storage_service=storage,
    )
    with pytest.raises(ValidationError):
        asyncio.run(
            use_case.execute(
                ReplaceMaskInput(
                    appearance_id=appearance_id,
                    nueva_ruta_archivo="/data/masks/new.png",
                    nuevo_hash_sha256="wronghash",
                )
            )
        )


def test_correct_mask_requires_correcciones():
    """correct_mask debe lanzar ValidationError si correcciones está vacío."""
    appearance_id = uuid.uuid4()
    artifact = StubArtifact(
        id=uuid.uuid4(),
        appearance_id=appearance_id,
        tipo_mascara="caracter",
        ruta_archivo="/data/masks/m1.png",
        hash_sha256="hash1",
        version=1,
    )
    repo = StubArtifactRepository([artifact])
    use_case = CorrectMaskUseCase(artifact_repository=repo)
    with pytest.raises(ValidationError):
        asyncio.run(
            use_case.execute(CorrectMaskInput(appearance_id=appearance_id, correcciones={}))
        )


def test_correct_mask_increments_version():
    """correct_mask debe incrementar la versión y registrar correcciones."""
    appearance_id = uuid.uuid4()
    artifact = StubArtifact(
        id=uuid.uuid4(),
        appearance_id=appearance_id,
        tipo_mascara="caracter",
        ruta_archivo="/data/masks/m1.png",
        hash_sha256="hash1",
        version=1,
    )
    repo = StubArtifactRepository([artifact])
    use_case = CorrectMaskUseCase(artifact_repository=repo)
    output = asyncio.run(
        use_case.execute(
            CorrectMaskInput(
                appearance_id=appearance_id,
                correcciones={"region_1": "ajustado"},
            )
        )
    )

    assert output.version == 2
    assert output.corregido is True
    assert output.correcciones == {"region_1": "ajustado"}

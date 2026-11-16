"""RED/GREEN tests for P5 character memory use cases (S2, S3, S5, S6).

Verifies GetCharacterMemory, UpdateCharacterMemory, AddCharacterReference,
ListCharacterAppearances with stub protocol repositories (no database
required).
"""

import asyncio
import uuid
from dataclasses import FrozenInstanceError, dataclass
from typing import Any

import pytest
from app.application.use_cases.add_character_reference import (
    AddCharacterReferenceInput,
    AddCharacterReferenceUseCase,
)
from app.application.use_cases.get_character_memory import (
    CharacterMemoryOutput,
    GetCharacterMemoryInput,
    GetCharacterMemoryUseCase,
)
from app.application.use_cases.list_character_appearances import (
    ListCharacterAppearancesOutput,
    ListCharacterAppearancesUseCase,
)
from app.application.use_cases.update_character_memory import (
    UpdateCharacterMemoryInput,
    UpdateCharacterMemoryUseCase,
)
from app.core.exceptions import NotFoundError, ValidationError


@dataclass
class StubMemory:
    id: uuid.UUID
    character_id: uuid.UUID
    embedding: str | None = None
    embedding_model: str | None = None
    atributos_estables: dict[str, Any] | None = None
    atributos_escena: dict[str, Any] | None = None
    referencia_estable: str | None = None
    pagina_origen_id: uuid.UUID | None = None
    created_at: Any = None
    updated_at: Any = None


@dataclass
class StubAppearance:
    id: uuid.UUID
    character_id: uuid.UUID
    page_id: uuid.UUID
    panel_id: uuid.UUID | None = None
    confianza_deteccion: float | None = None
    created_at: Any = None


class StubMemoryRepository:
    def __init__(self, memories: list[StubMemory]):
        self._memories = {m.character_id: m for m in memories}
        self.updated: dict[uuid.UUID, dict[str, Any]] = {}

    async def get_by_character(
        self, *, character_id: uuid.UUID
    ) -> StubMemory | None:
        return self._memories.get(character_id)

    async def update(
        self,
        *,
        memory_id: uuid.UUID,
        **kwargs: Any,
    ) -> StubMemory | None:
        memory = None
        for m in self._memories.values():
            if m.id == memory_id:
                memory = m
                break
        if memory is None:
            return None
        if "atributos_estables" in kwargs:
            memory.atributos_estables = kwargs["atributos_estables"]
        if "atributos_escena" in kwargs:
            memory.atributos_escena = kwargs["atributos_escena"]
        if "referencia_estable" in kwargs:
            memory.referencia_estable = kwargs["referencia_estable"]
        self.updated[memory_id] = {
            "atributos_estables": memory.atributos_estables,
            "atributos_escena": memory.atributos_escena,
            "referencia_estable": memory.referencia_estable,
        }
        return memory

    async def create(self, **kwargs: Any) -> StubMemory:
        cid = kwargs.get("character_id", uuid.uuid4())
        memory = StubMemory(
            id=kwargs.get("id", uuid.uuid4()),
            character_id=cid,
            embedding=kwargs.get("embedding"),
            atributos_estables=kwargs.get("atributos_estables"),
            atributos_escena=kwargs.get("atributos_escena"),
            referencia_estable=kwargs.get("referencia_estable"),
        )
        self._memories[cid] = memory
        return memory


class StubAppearanceRepository:
    def __init__(self, appearances: list[StubAppearance]):
        self._appearances = appearances

    async def list_by_character(
        self, *, character_id: uuid.UUID
    ) -> list[StubAppearance]:
        return [a for a in self._appearances if a.character_id == character_id]


def test_output_dtos_are_frozen():
    """DTOs must be frozen dataclasses (immutable)."""
    output = CharacterMemoryOutput(
        character_id="c1",
        embedding=None,
        embedding_model=None,
        atributos_estables=None,
        atributos_escena=None,
        referencia_estable=None,
        pagina_origen_id=None,
        created_at=None,
        updated_at=None,
    )
    with pytest.raises(FrozenInstanceError):
        output.referencia_estable = "x"

    output2 = ListCharacterAppearancesOutput(
        character_id="c1",
        appearances=[],
        total=0,
    )
    with pytest.raises(FrozenInstanceError):
        output2.total = 1


def test_get_character_memory_happy_path():
    """Debe retornar la memoria del personaje."""
    character_id = uuid.uuid4()
    memory = StubMemory(
        id=uuid.uuid4(),
        character_id=character_id,
        atributos_estables={"cabello": "negro", "ojos": "café"},
        atributos_escena={"vestimenta": "gakuran"},
        referencia_estable="ref-001",
    )
    repo = StubMemoryRepository([memory])
    use_case = GetCharacterMemoryUseCase(character_memory_repository=repo)
    output = asyncio.run(
        use_case.execute(GetCharacterMemoryInput(character_id=character_id))
    )

    assert output.character_id == str(character_id)
    assert output.atributos_estables == {"cabello": "negro", "ojos": "café"}
    assert output.atributos_escena == {"vestimenta": "gakuran"}
    assert output.referencia_estable == "ref-001"


def test_get_character_memory_not_found():
    """Debe lanzar NotFoundError si no existe memoria del personaje."""
    use_case = GetCharacterMemoryUseCase(
        character_memory_repository=StubMemoryRepository([])
    )
    with pytest.raises(NotFoundError):
        asyncio.run(
            use_case.execute(GetCharacterMemoryInput(character_id=uuid.uuid4()))
        )


def test_update_character_memory_preserves_unchanged():
    """update_character_memory debe preservar campos no enviados."""
    character_id = uuid.uuid4()
    memory_id = uuid.uuid4()
    memory = StubMemory(
        id=memory_id,
        character_id=character_id,
        atributos_estables={"cabello": "negro"},
        atributos_escena={"vestimenta": "gakuran"},
    )
    repo = StubMemoryRepository([memory])
    use_case = UpdateCharacterMemoryUseCase(character_memory_repository=repo)
    output = asyncio.run(
        use_case.execute(
            UpdateCharacterMemoryInput(
                character_id=character_id,
                atributos_escena={"vestimenta": "blusa"},
            )
        )
    )

    assert output.atributos_estables == {"cabello": "negro"}
    assert output.atributos_escena == {"vestimenta": "blusa"}
    assert repo.updated[memory_id]["atributos_estables"] == {"cabello": "negro"}


def test_update_character_memory_requires_at_least_one_field():
    """Sin campos modificables debe lanzar ValidationError."""
    character_id = uuid.uuid4()
    repo = StubMemoryRepository([])
    use_case = UpdateCharacterMemoryUseCase(
        character_memory_repository=repo
    )
    with pytest.raises(ValidationError):
        asyncio.run(
            use_case.execute(UpdateCharacterMemoryInput(character_id=character_id))
        )


def test_update_character_memory_not_found():
    """Debe lanzar NotFoundError si el personaje no tiene memoria."""
    use_case = UpdateCharacterMemoryUseCase(
        character_memory_repository=StubMemoryRepository([])
    )
    with pytest.raises(NotFoundError):
        asyncio.run(
            use_case.execute(
                UpdateCharacterMemoryInput(
                    character_id=uuid.uuid4(),
                    atributos_estables={"cabello": "negro"},
                )
            )
        )


def test_add_character_reference_create():
    """add_character_reference debe crear memoria si no existe."""
    character_id = uuid.uuid4()
    repo = StubMemoryRepository([])
    use_case = AddCharacterReferenceUseCase(character_memory_repository=repo)
    output = asyncio.run(
        use_case.execute(
            AddCharacterReferenceInput(
                character_id=character_id,
                referencia_estable="ref-001",
            )
        )
    )

    assert output.referencia_estable == "ref-001"


def test_add_character_reference_update():
    """add_character_reference debe actualizar si ya existe."""
    character_id = uuid.uuid4()
    memory = StubMemory(id=uuid.uuid4(), character_id=character_id)
    repo = StubMemoryRepository([memory])
    use_case = AddCharacterReferenceUseCase(character_memory_repository=repo)
    output = asyncio.run(
        use_case.execute(
            AddCharacterReferenceInput(
                character_id=character_id,
                referencia_estable="ref-002",
            )
        )
    )

    assert output.referencia_estable == "ref-002"


def test_add_character_reference_empty_rejects():
    """referencia_estable vacía debe lanzar ValidationError."""
    use_case = AddCharacterReferenceUseCase(
        character_memory_repository=StubMemoryRepository([])
    )
    with pytest.raises(ValidationError):
        asyncio.run(
            use_case.execute(
                AddCharacterReferenceInput(
                    character_id=uuid.uuid4(), referencia_estable="  "
                )
            )
        )


def test_list_character_appearances():
    """Debe listar las apariciones de un personaje."""
    character_id = uuid.uuid4()
    page_id = uuid.uuid4()
    appearances = [
        StubAppearance(id=uuid.uuid4(), character_id=character_id, page_id=page_id),
        StubAppearance(id=uuid.uuid4(), character_id=character_id, page_id=page_id),
    ]
    repo = StubAppearanceRepository(appearances)
    use_case = ListCharacterAppearancesUseCase(
        character_appearance_repository=repo
    )
    output = asyncio.run(
        use_case.execute(character_id=character_id)
    )

    assert output.total == 2
    assert len(output.appearances) == 2


def test_list_character_appearances_not_found_when_empty():
    """Sin apariciones debe lanzar NotFoundError."""
    use_case = ListCharacterAppearancesUseCase(
        character_appearance_repository=StubAppearanceRepository([])
    )
    with pytest.raises(NotFoundError):
        asyncio.run(
            use_case.execute(character_id=uuid.uuid4())
        )

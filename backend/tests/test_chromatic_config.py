"""RED/GREEN tests for P6 chromatic configuration use cases (S1, S2, S8).

Verifies edit/approve attribute and palette use cases with stub protocol
repositories (no database required).
"""

import asyncio
import uuid
from dataclasses import FrozenInstanceError, dataclass
from typing import Any

import pytest

from app.application.use_cases.approve_character_attribute import (
    ApproveCharacterAttributeInput,
    ApproveCharacterAttributeUseCase,
)
from app.application.use_cases.approve_character_palette import (
    ApproveCharacterPaletteInput,
    ApproveCharacterPaletteUseCase,
)
from app.application.use_cases.edit_character_attribute import (
    EditCharacterAttributeInput,
    EditCharacterAttributeUseCase,
)
from app.application.use_cases.edit_character_palette import (
    EditCharacterPaletteInput,
    EditCharacterPaletteUseCase,
)
from app.core.exceptions import NotFoundError, ValidationError


@dataclass
class StubAttribute:
    id: uuid.UUID
    character_id: uuid.UUID
    nombre_atributo: str
    valor_sugerido: str | None = None
    valor_aprobado: str | None = None
    esta_aprobado: bool = False
    confianza_sugerencia: float | None = None


@dataclass
class StubPalette:
    id: uuid.UUID
    character_id: uuid.UUID
    nombre_color: str
    valor_hex: str | None = None
    esta_aprobado: bool = False


class StubAttributeRepository:
    def __init__(self, attributes: list[StubAttribute]):
        self._attrs = {a.id: a for a in attributes}
        self.updated: dict[uuid.UUID, dict[str, Any]] = {}

    async def get_by_character_and_name(
        self,
        *,
        character_id: uuid.UUID,
        nombre_atributo: str,
    ) -> StubAttribute | None:
        for a in self._attrs.values():
            if a.character_id == character_id and a.nombre_atributo == nombre_atributo:
                return a
        return None

    async def create(self, **kwargs: Any) -> StubAttribute:
        aid = kwargs.get("id", uuid.uuid4())
        attr = StubAttribute(
            id=aid,
            character_id=kwargs["character_id"],
            nombre_atributo=kwargs["nombre_atributo"],
            valor_sugerido=kwargs.get("valor_sugerido"),
            confianza_sugerencia=kwargs.get("confianza_sugerencia"),
        )
        self._attrs[aid] = attr
        return attr

    async def update(
        self,
        attribute_id: uuid.UUID,
        **kwargs: Any,
    ) -> StubAttribute | None:
        attr = self._attrs.get(attribute_id)
        if attr is None:
            return None
        for key, value in kwargs.items():
            setattr(attr, key, value)
        self.updated[attribute_id] = {
            "valor_sugerido": attr.valor_sugerido,
            "valor_aprobado": attr.valor_aprobado,
            "esta_aprobado": attr.esta_aprobado,
        }
        return attr


class StubPaletteRepository:
    def __init__(self, palettes: list[StubPalette]):
        self._palettes = {p.id: p for p in palettes}
        self.updated: dict[uuid.UUID, dict[str, Any]] = {}

    async def get_by_character_and_name(
        self,
        *,
        character_id: uuid.UUID,
        nombre_color: str,
    ) -> StubPalette | None:
        for p in self._palettes.values():
            if p.character_id == character_id and p.nombre_color == nombre_color:
                return p
        return None

    async def create(self, **kwargs: Any) -> StubPalette:
        pid = kwargs.get("id", uuid.uuid4())
        pal = StubPalette(
            id=pid,
            character_id=kwargs["character_id"],
            nombre_color=kwargs["nombre_color"],
            valor_hex=kwargs.get("valor_hex"),
        )
        self._palettes[pid] = pal
        return pal

    async def update(
        self,
        palette_id: uuid.UUID,
        **kwargs: Any,
    ) -> StubPalette | None:
        pal = self._palettes.get(palette_id)
        if pal is None:
            return None
        for key, value in kwargs.items():
            setattr(pal, key, value)
        self.updated[palette_id] = {
            "valor_hex": pal.valor_hex,
            "esta_aprobado": pal.esta_aprobado,
        }
        return pal


def test_dtos_are_frozen():
    """DTOs must be frozen dataclasses (immutable)."""
    inp = EditCharacterAttributeInput(
        character_id=uuid.uuid4(),
        nombre_atributo="cabello",
        valor_sugerido="#000000",
    )
    with pytest.raises(FrozenInstanceError):
        inp.valor_sugerido = "#ffffff"


def test_edit_character_attribute_creates_new():
    """Debe crear un atributo cuando no existe."""
    character_id = uuid.uuid4()
    repo = StubAttributeRepository([])
    use_case = EditCharacterAttributeUseCase(character_attribute_repository=repo)
    output = asyncio.run(
        use_case.execute(
            EditCharacterAttributeInput(
                character_id=character_id,
                nombre_atributo="cabello",
                valor_sugerido="negro",
                confianza_sugerencia=0.8,
            )
        )
    )

    assert output.nombre_atributo == "cabello"
    assert output.valor_sugerido == "negro"
    assert output.confianza_sugerencia == 0.8


def test_edit_character_attribute_updates_existing():
    """Debe actualizar un atributo existente."""
    character_id = uuid.uuid4()
    attr_id = uuid.uuid4()
    attr = StubAttribute(
        id=attr_id,
        character_id=character_id,
        nombre_atributo="cabello",
        valor_sugerido="negro",
    )
    repo = StubAttributeRepository([attr])
    use_case = EditCharacterAttributeUseCase(character_attribute_repository=repo)
    output = asyncio.run(
        use_case.execute(
            EditCharacterAttributeInput(
                character_id=character_id,
                nombre_atributo="cabello",
                valor_sugerido="castaño",
            )
        )
    )

    assert output.valor_sugerido == "castaño"
    assert repo.updated[attr_id]["valor_sugerido"] == "castaño"


def test_approve_character_attribute_requires_suggestion():
    """No se puede aprobar un atributo sin valor sugerido."""
    character_id = uuid.uuid4()
    attr_id = uuid.uuid4()
    attr = StubAttribute(
        id=attr_id,
        character_id=character_id,
        nombre_atributo="cabello",
        valor_sugerido=None,
    )
    repo = StubAttributeRepository([attr])
    use_case = ApproveCharacterAttributeUseCase(character_attribute_repository=repo)
    with pytest.raises(ValidationError):
        asyncio.run(
            use_case.execute(
                ApproveCharacterAttributeInput(
                    character_id=character_id,
                    nombre_atributo="cabello",
                )
            )
        )


def test_approve_character_attribute_happy_path():
    """Debe marcar el atributo como aprobado con el valor sugerido."""
    character_id = uuid.uuid4()
    attr_id = uuid.uuid4()
    attr = StubAttribute(
        id=attr_id,
        character_id=character_id,
        nombre_atributo="cabello",
        valor_sugerido="negro",
    )
    repo = StubAttributeRepository([attr])
    use_case = ApproveCharacterAttributeUseCase(character_attribute_repository=repo)
    output = asyncio.run(
        use_case.execute(
            ApproveCharacterAttributeInput(
                character_id=character_id,
                nombre_atributo="cabello",
            )
        )
    )

    assert output.esta_aprobado is True
    assert output.valor_aprobado == "negro"
    assert repo.updated[attr_id]["esta_aprobado"] is True


def test_approve_character_attribute_not_found():
    """Debe lanzar NotFoundError si el atributo no existe."""
    use_case = ApproveCharacterAttributeUseCase(
        character_attribute_repository=StubAttributeRepository([])
    )
    with pytest.raises(NotFoundError):
        asyncio.run(
            use_case.execute(
                ApproveCharacterAttributeInput(
                    character_id=uuid.uuid4(),
                    nombre_atributo="cabello",
                )
            )
        )


def test_edit_character_palette_creates_new():
    """Debe crear una paleta cuando no existe."""
    character_id = uuid.uuid4()
    repo = StubPaletteRepository([])
    use_case = EditCharacterPaletteUseCase(character_palette_repository=repo)
    output = asyncio.run(
        use_case.execute(
            EditCharacterPaletteInput(
                character_id=character_id,
                nombre_color="color_base",
                valor_hex="#ff5733",
            )
        )
    )

    assert output.nombre_color == "color_base"
    assert output.valor_hex == "#ff5733"


def test_approve_character_palette_requires_suggestion():
    """No se puede aprobar una paleta sin valor hex."""
    character_id = uuid.uuid4()
    pal_id = uuid.uuid4()
    pal = StubPalette(
        id=pal_id,
        character_id=character_id,
        nombre_color="color_base",
        valor_hex=None,
    )
    repo = StubPaletteRepository([pal])
    use_case = ApproveCharacterPaletteUseCase(character_palette_repository=repo)
    with pytest.raises(ValidationError):
        asyncio.run(
            use_case.execute(
                ApproveCharacterPaletteInput(
                    character_id=character_id,
                    nombre_color="color_base",
                )
            )
        )


def test_approve_character_palette_happy_path():
    """Debe marcar la paleta como aprobada con el valor hex."""
    character_id = uuid.uuid4()
    pal_id = uuid.uuid4()
    pal = StubPalette(
        id=pal_id,
        character_id=character_id,
        nombre_color="color_base",
        valor_hex="#ff5733",
    )
    repo = StubPaletteRepository([pal])
    use_case = ApproveCharacterPaletteUseCase(character_palette_repository=repo)
    output = asyncio.run(
        use_case.execute(
            ApproveCharacterPaletteInput(
                character_id=character_id,
                nombre_color="color_base",
            )
        )
    )

    assert output.esta_aprobado is True

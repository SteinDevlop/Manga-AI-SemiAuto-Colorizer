"""RED/GREEN tests for P4 identity use cases (S4).

Verifies GroupIdentitiesUseCase and ReviewIdentityUseCase with stub
protocol implementations (no database required).
"""

import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pytest

from app.application.use_cases.group_identities import (
    GroupIdentitiesInput,
    GroupIdentitiesUseCase,
)
from app.application.use_cases.review_identity import (
    ReviewIdentityInput,
    ReviewIdentityUseCase,
)
from app.core.exceptions import NotFoundError, ValidationError


@dataclass
class StubAppearance:
    id: uuid.UUID
    page_id: uuid.UUID
    character_id: uuid.UUID | None = None
    panel_id: uuid.UUID | None = None
    confianza_deteccion: float | None = None
    created_at: Any = datetime.now(timezone.utc)


@dataclass
class StubAnalysis:
    id: uuid.UUID
    page_id: uuid.UUID
    estado: str = "analysis_pending"


class StubAnalysisRepository:
    def __init__(self, analyses: dict[uuid.UUID, StubAnalysis]):
        self._analyses = analyses

    async def get(self, *, analysis_id: uuid.UUID) -> StubAnalysis | None:
        return self._analyses.get(analysis_id)


class StubAppearanceRepository:
    def __init__(self, appearances: list[StubAppearance]):
        self._appearances = {a.id: a for a in appearances}
        self.updated: dict[uuid.UUID, uuid.UUID] = {}

    async def list_by_page(self, *, page_id: uuid.UUID) -> list[StubAppearance]:
        return [a for a in self._appearances.values() if a.page_id == page_id]

    async def get(self, *, appearance_id: uuid.UUID) -> StubAppearance | None:
        return self._appearances.get(appearance_id)

    async def update_character(
        self, *, appearance_id: uuid.UUID, character_id: uuid.UUID
    ) -> StubAppearance | None:
        self.updated[appearance_id] = character_id
        a = self._appearances.get(appearance_id)
        if a is not None:
            a.character_id = character_id
        return a


class StubCharacterRepository:
    def __init__(self):
        self._characters: dict[uuid.UUID, dict[str, Any]] = {}
        self.created: list[dict[str, Any]] = []

    async def create(
        self,
        *,
        nombre: str,
        descripcion: str | None,
        confianza_identidad: float | None,
    ) -> Any:
        cid = uuid.uuid4()
        entity = type(
            "Character",
            (),
            {
                "id": cid,
                "nombre": nombre,
                "descripcion": descripcion,
                "confianza_identidad": confianza_identidad,
            },
        )()
        self._characters[cid] = {
            "id": cid,
            "nombre": nombre,
            "descripcion": descripcion,
            "confianza_identidad": confianza_identidad,
        }
        self.created.append(self._characters[cid])
        return entity

    async def get(self, *, character_id: uuid.UUID) -> dict[str, Any] | None:
        return self._characters.get(character_id)


class StubCharacterMatcher:
    def __init__(self, proposals: list[dict]):
        self._proposals = proposals

    def match(self, appearances: list[dict]) -> list[dict]:
        return list(self._proposals)


def test_group_identities_happy_path():
    """Debe crear personajes y asociar apariciones con el matcher."""
    analysis_id = uuid.uuid4()
    page_id = uuid.uuid4()
    appearance_ids = [uuid.uuid4(), uuid.uuid4()]

    analysis_repo = StubAnalysisRepository(
        {analysis_id: StubAnalysis(analysis_id, page_id)}
    )
    appearance_repo = StubAppearanceRepository(
        [
            StubAppearance(id=appearance_ids[0], page_id=page_id, confianza_deteccion=0.9),
            StubAppearance(id=appearance_ids[1], page_id=page_id, confianza_deteccion=0.85),
        ]
    )
    char_repo = StubCharacterRepository()
    matcher = StubCharacterMatcher(
        [
            {
                "apariciones": [str(a) for a in appearance_ids],
                "confianza_identidad": 0.96,
                "nombre_sugerido": "Protagonista",
            }
        ]
    )

    use_case = GroupIdentitiesUseCase(
        analysis_repository=analysis_repo,
        appearance_repository=appearance_repo,
        character_repository=char_repo,
        matcher=matcher,
    )
    output = asyncio.run(use_case.execute(GroupIdentitiesInput(analysis_id=analysis_id)))

    assert output.total_appearances == 2
    assert len(output.identities) == 1
    assert output.identities[0].nombre == "Protagonista"
    assert output.identities[0].confianza_identidad == 0.96
    assert appearance_repo.updated[appearance_ids[0]] is not None


def test_group_identities_missing_analysis():
    """Debe lanzar NotFoundError si el análisis no existe."""
    use_case = GroupIdentitiesUseCase(
        analysis_repository=StubAnalysisRepository({}),
        appearance_repository=StubAppearanceRepository([]),
        character_repository=StubCharacterRepository(),
        matcher=StubCharacterMatcher([]),
    )
    with pytest.raises(NotFoundError):
        asyncio.run(use_case.execute(GroupIdentitiesInput(analysis_id=uuid.uuid4())))


def test_group_identities_malformed_proposal():
    """Debe lanzar ValidationError si el matcher devuelve propuesta sin apariciones."""
    analysis_id = uuid.uuid4()
    page_id = uuid.uuid4()
    analysis_repo = StubAnalysisRepository({analysis_id: StubAnalysis(analysis_id, page_id)})
    matcher = StubCharacterMatcher(
        [{"apariciones": [], "confianza_identidad": 0.5, "nombre_sugerido": "X"}]
    )
    use_case = GroupIdentitiesUseCase(
        analysis_repository=analysis_repo,
        appearance_repository=StubAppearanceRepository([]),
        character_repository=StubCharacterRepository(),
        matcher=matcher,
    )
    with pytest.raises(ValidationError):
        asyncio.run(use_case.execute(GroupIdentitiesInput(analysis_id=analysis_id)))


def test_review_identity_requires_character_id():
    """character_id None debe lanzar ValidationError al ejecutar (human-in-the-loop)."""
    use_case = ReviewIdentityUseCase(
        appearance_repository=StubAppearanceRepository([]),
        character_repository=StubCharacterRepository(),
    )
    with pytest.raises(ValidationError):
        asyncio.run(
            use_case.execute(
                ReviewIdentityInput(appearance_id=uuid.uuid4(), character_id=None)
            )
        )


def test_review_identity_happy_path():
    """Debe actualizar appearance.character_id y retornar DTO."""
    appearance_id = uuid.uuid4()
    character_id = uuid.uuid4()
    page_id = uuid.uuid4()

    appearance = StubAppearance(
        id=appearance_id,
        page_id=page_id,
        confianza_deteccion=0.88,
    )

    appearance_repo = StubAppearanceRepository([appearance])
    char_repo = StubCharacterRepository()

    async def stub_char_get(*, character_id: uuid.UUID):
        return {"id": character_id, "nombre": "Test"}

    char_repo.get = stub_char_get

    use_case = ReviewIdentityUseCase(
        appearance_repository=appearance_repo,
        character_repository=char_repo,
    )
    output = asyncio.run(
        use_case.execute(
            ReviewIdentityInput(appearance_id=appearance_id, character_id=character_id)
        )
    )

    assert output.id == str(appearance_id)
    assert output.character_id == str(character_id)
    assert appearance_repo.updated[appearance_id] == character_id


def test_review_identity_missing_appearance():
    """Debe lanzar NotFoundError si la apariencia no existe."""
    use_case = ReviewIdentityUseCase(
        appearance_repository=StubAppearanceRepository([]),
        character_repository=StubCharacterRepository(),
    )
    with pytest.raises(NotFoundError):
        asyncio.run(
            use_case.execute(
                ReviewIdentityInput(
                    appearance_id=uuid.uuid4(), character_id=uuid.uuid4()
                )
            )
        )

"""HTTP endpoints for character identity and chromatic configuration."""
from __future__ import annotations
from typing import Any
from uuid import UUID
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError
from app.infrastructure.database.session import get_session
from app.modules.page_analysis.repositories import AnalysisRepository
from app.modules.character_analysis.repositories import CharacterAppearanceRepository, CharacterRepository
from app.modules.character_configuration.repositories import CharacterAttributeRepository, CharacterPaletteRepository
from app.application.use_cases.edit_character_attribute import EditCharacterAttributeInput, EditCharacterAttributeUseCase
from app.application.use_cases.approve_character_attribute import ApproveCharacterAttributeInput, ApproveCharacterAttributeUseCase
from app.application.use_cases.edit_character_palette import EditCharacterPaletteInput, EditCharacterPaletteUseCase
from app.application.use_cases.approve_character_palette import ApproveCharacterPaletteInput, ApproveCharacterPaletteUseCase
from app.application.use_cases.add_character_reference import AddCharacterReferenceInput, AddCharacterReferenceUseCase
from app.application.use_cases.get_character_memory import GetCharacterMemoryInput, GetCharacterMemoryUseCase
from app.application.use_cases.update_character_memory import UpdateCharacterMemoryInput, UpdateCharacterMemoryUseCase
from app.application.use_cases.list_character_appearances import ListCharacterAppearancesUseCase
from app.application.use_cases.review_identity import ReviewIdentityInput, ReviewIdentityUseCase
from app.application.use_cases.group_identities import GroupIdentitiesInput, GroupIdentitiesUseCase
from app.modules.character_memory.repositories import CharacterMemoryRepository
from app.ai_engine.adapters.mock.character_matcher import MockCharacterMatcher

router = APIRouter(prefix="/api/v1", tags=["characters"])

class AttributeBody(BaseModel):
    valor_sugerido: str = Field(min_length=1, max_length=200)
    confianza_sugerencia: float | None = Field(default=None, ge=0, le=1)

class PaletteBody(BaseModel):
    valor_hex: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")

class IdentityReviewBody(BaseModel):
    character_id: UUID

class StableReferenceBody(BaseModel):
    referencia_estable: str = Field(min_length=1, max_length=512)

class CharacterMemoryBody(BaseModel):
    atributos_estables: dict[str, Any] | None = None
    atributos_escena: dict[str, Any] | None = None
    referencia_estable: str | None = Field(default=None, max_length=512)

@router.get("/analysis/{analysis_id}/characters")
async def list_analysis_characters(analysis_id: UUID, session: AsyncSession = Depends(get_session)):
    analysis = await AnalysisRepository(session).get(analysis_id)
    if analysis is None:
        raise NotFoundError("Analysis not found.")
    appearances = await CharacterAppearanceRepository(session).list(page_id=analysis.page_id)
    character_repo = CharacterRepository(session)
    attributes_repo = CharacterAttributeRepository(session)
    palettes_repo = CharacterPaletteRepository(session)
    ids = list(dict.fromkeys(a.character_id for a in appearances))
    result = []
    for character_id in ids:
        character = await character_repo.get(character_id)
        if character is None:
            continue
        attributes = await attributes_repo.list(character_id)
        palettes = await palettes_repo.list(character_id)
        result.append({
            "id": str(character.id), "nombre": character.nombre,
            "descripcion": character.descripcion,
            "confianza_identidad": character.confianza_identidad,
            "appearances": [{"id": str(a.id), "page_id": str(a.page_id), "panel_id": str(a.panel_id) if a.panel_id else None} for a in appearances if a.character_id == character_id],
            "attributes": [{"id": str(a.id), "nombre_atributo": a.nombre_atributo, "valor_sugerido": a.valor_sugerido, "valor_aprobado": a.valor_aprobado, "esta_aprobado": a.esta_aprobado, "confianza_sugerencia": a.confianza_sugerencia} for a in attributes],
            "palettes": [{"id": str(p.id), "nombre_color": p.nombre_color, "valor_hex": p.valor_hex, "esta_aprobado": p.esta_aprobado} for p in palettes],
        })
    return result

@router.patch("/characters/{character_id}/attributes/{name}")
async def edit_attribute(character_id: UUID, name: str, body: AttributeBody, session: AsyncSession = Depends(get_session)):
    if await CharacterRepository(session).get(character_id) is None:
        raise NotFoundError("Character not found.")
    output = await EditCharacterAttributeUseCase(character_attribute_repository=CharacterAttributeRepository(session)).execute(
        EditCharacterAttributeInput(character_id=character_id, nombre_atributo=name, valor_sugerido=body.valor_sugerido, confianza_sugerencia=body.confianza_sugerencia)
    )
    return output.__dict__

@router.post("/characters/{character_id}/attributes/{name}/approve")
async def approve_attribute(character_id: UUID, name: str, session: AsyncSession = Depends(get_session)):
    output = await ApproveCharacterAttributeUseCase(character_attribute_repository=CharacterAttributeRepository(session)).execute(
        ApproveCharacterAttributeInput(character_id=character_id, nombre_atributo=name)
    )
    return output.__dict__

@router.patch("/characters/{character_id}/palettes/{name}")
async def edit_palette(character_id: UUID, name: str, body: PaletteBody, session: AsyncSession = Depends(get_session)):
    if await CharacterRepository(session).get(character_id) is None:
        raise NotFoundError("Character not found.")
    output = await EditCharacterPaletteUseCase(character_palette_repository=CharacterPaletteRepository(session)).execute(
        EditCharacterPaletteInput(character_id=character_id, nombre_color=name, valor_hex=body.valor_hex)
    )
    return output.__dict__

@router.post("/characters/{character_id}/palettes/{name}/approve")
async def approve_palette(character_id: UUID, name: str, session: AsyncSession = Depends(get_session)):
    output = await ApproveCharacterPaletteUseCase(character_palette_repository=CharacterPaletteRepository(session)).execute(
        ApproveCharacterPaletteInput(character_id=character_id, nombre_color=name)
    )
    return output.__dict__

@router.get("/characters/{character_id}/appearances")
async def list_character_appearances(character_id: UUID, session: AsyncSession = Depends(get_session)):
    output = await ListCharacterAppearancesUseCase(CharacterAppearanceRepository(session)).execute(character_id)
    return output.__dict__

@router.patch("/appearances/{appearance_id}/identity")
async def review_identity(appearance_id: UUID, body: IdentityReviewBody, session: AsyncSession = Depends(get_session)):
    output = await ReviewIdentityUseCase(
        appearance_repository=CharacterAppearanceRepository(session),
        character_repository=CharacterRepository(session),
    ).execute(ReviewIdentityInput(appearance_id=appearance_id, character_id=body.character_id))
    return output.__dict__

@router.post("/analysis/{analysis_id}/group-identities")
async def group_analysis_identities(analysis_id: UUID, session: AsyncSession = Depends(get_session)):
    output = await GroupIdentitiesUseCase(
        analysis_repository=AnalysisRepository(session),
        appearance_repository=CharacterAppearanceRepository(session),
        character_repository=CharacterRepository(session),
        matcher=MockCharacterMatcher(),
    ).execute(GroupIdentitiesInput(analysis_id=analysis_id))
    return {
        "analysis_id": output.analysis_id,
        "total_appearances": output.total_appearances,
        "identities": [identity.__dict__ for identity in output.identities],
    }

@router.put("/characters/{character_id}/reference")
async def add_character_reference(character_id: UUID, body: StableReferenceBody, session: AsyncSession = Depends(get_session)):
    if await CharacterRepository(session).get(character_id) is None:
        raise NotFoundError("Character not found.")
    output = await AddCharacterReferenceUseCase(CharacterMemoryRepository(session)).execute(
        AddCharacterReferenceInput(character_id=character_id, referencia_estable=body.referencia_estable)
    )
    return output.__dict__

@router.get("/characters/{character_id}/memory")
async def get_character_memory(character_id: UUID, session: AsyncSession = Depends(get_session)):
    output = await GetCharacterMemoryUseCase(CharacterMemoryRepository(session)).execute(
        GetCharacterMemoryInput(character_id=character_id)
    )
    return output.__dict__

@router.patch("/characters/{character_id}/memory")
async def update_character_memory(character_id: UUID, body: CharacterMemoryBody, session: AsyncSession = Depends(get_session)):
    output = await UpdateCharacterMemoryUseCase(CharacterMemoryRepository(session)).execute(
        UpdateCharacterMemoryInput(
            character_id=character_id,
            atributos_estables=body.atributos_estables,
            atributos_escena=body.atributos_escena,
            referencia_estable=body.referencia_estable,
        )
    )
    return output.__dict__

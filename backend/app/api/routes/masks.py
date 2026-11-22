"""HTTP endpoints for listing and reviewing analysis masks."""
from __future__ import annotations
from uuid import UUID
from typing import Any
from pathlib import Path
import mimetypes
import tempfile
import os
from io import BytesIO
from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse
from PIL import Image
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError, ForbiddenError
from app.core.config import get_settings
from app.infrastructure.database.session import get_session
from app.modules.page_analysis.repositories import AnalysisRepository
from app.modules.character_analysis.repositories import CharacterAppearanceRepository
from app.modules.colorization.repositories import MaskArtifactRepository
from app.application.use_cases.correct_mask import CorrectMaskInput, CorrectMaskUseCase
from app.application.use_cases.edit_mask import EditMaskInput, EditMaskUseCase
from app.application.use_cases.replace_mask import ReplaceMaskInput, ReplaceMaskUseCase
from app.infrastructure.storage.service import StorageService

router = APIRouter(prefix="/api/v1", tags=["masks"])

class MaskCorrectionBody(BaseModel):
    correcciones: dict[str, Any] = Field(min_length=1)

@router.get("/analysis/{analysis_id}/masks")
async def list_analysis_masks(analysis_id: UUID, session: AsyncSession = Depends(get_session)):
    analysis = await AnalysisRepository(session).get(analysis_id)
    if analysis is None:
        raise NotFoundError("Analysis not found.")
    appearances = await CharacterAppearanceRepository(session).list(page_id=analysis.page_id)
    repository = MaskArtifactRepository(session)
    masks = []
    for appearance in appearances:
        for mask in await repository.list_by_appearance(appearance_id=appearance.id):
            masks.append({
                "id": str(mask.id), "appearance_id": str(mask.appearance_id),
                "tipo_mascara": mask.tipo_mascara, "ruta_archivo": mask.ruta_archivo,
                "hash_sha256": mask.hash_sha256, "version": mask.version,
                "corregido": mask.corregido, "correcciones": mask.correcciones,
            })
    return masks

@router.patch("/appearances/{appearance_id}/mask/correct")
async def correct_appearance_mask(appearance_id: UUID, body: MaskCorrectionBody, session: AsyncSession = Depends(get_session)):
    output = await CorrectMaskUseCase(artifact_repository=MaskArtifactRepository(session)).execute(
        CorrectMaskInput(appearance_id=appearance_id, correcciones=body.correcciones)
    )
    return output.__dict__

@router.get("/masks/{mask_id}/content")
async def get_mask_content(mask_id: UUID, session: AsyncSession = Depends(get_session)):
    """Serve mask image bytes only to authenticated users and only inside STORAGE_ROOT."""
    mask = await MaskArtifactRepository(session).get(mask_id)
    if mask is None:
        raise NotFoundError("Mask not found.")
    path = Path(mask.ruta_archivo).resolve()
    storage_root = Path(get_settings().STORAGE_ROOT).resolve()
    if not path.is_relative_to(storage_root):
        raise ForbiddenError("Mask path is outside the configured storage directory.")
    if not path.is_file():
        raise NotFoundError("Mask file not found.")
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return FileResponse(path, media_type=media_type, filename=path.name)

async def _save_mask_upload(file: UploadFile) -> dict[str, Any]:
    """Validate an uploaded raster image and store it under the private masks area."""
    settings = get_settings()
    content = await file.read(settings.MAX_UPLOAD_BYTES + 1)
    if not content:
        raise ValueError("El archivo de máscara está vacío.")
    if len(content) > settings.MAX_UPLOAD_BYTES:
        raise ValueError("El archivo de máscara supera el tamaño máximo permitido.")
    suffix = Path(file.filename or "mask.png").suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise ValueError("Formato de máscara no admitido. Usa PNG, JPG o WebP.")
    try:
        with Image.open(BytesIO(content)) as image:
            image.verify()
    except Exception as exc:
        raise ValueError("El archivo no contiene una imagen válida.") from exc
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        return StorageService().save(
            source_path=tmp_path, artifact_type="masks", original_name=file.filename or f"mask{suffix}"
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

@router.post("/appearances/{appearance_id}/mask")
async def edit_appearance_mask(
    appearance_id: UUID,
    tipo_mascara: str = Form(...),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    if await CharacterAppearanceRepository(session).get(appearance_id) is None:
        raise NotFoundError("Character appearance not found.")
    try:
        saved = await _save_mask_upload(file)
        output = await EditMaskUseCase(
            artifact_repository=MaskArtifactRepository(session), storage_service=StorageService()
        ).execute(EditMaskInput(
            appearance_id=appearance_id, tipo_mascara=tipo_mascara,
            ruta_archivo=saved["ruta_archivo"], hash_sha256=saved["hash_sha256"],
        ))
        return output.__dict__
    except ValueError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.put("/appearances/{appearance_id}/mask/replace")
async def replace_appearance_mask(
    appearance_id: UUID,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    if await CharacterAppearanceRepository(session).get(appearance_id) is None:
        raise NotFoundError("Character appearance not found.")
    try:
        saved = await _save_mask_upload(file)
        output = await ReplaceMaskUseCase(
            artifact_repository=MaskArtifactRepository(session), storage_service=StorageService()
        ).execute(ReplaceMaskInput(
            appearance_id=appearance_id, nueva_ruta_archivo=saved["ruta_archivo"],
            nuevo_hash_sha256=saved["hash_sha256"],
        ))
        return output.__dict__
    except ValueError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(exc)) from exc

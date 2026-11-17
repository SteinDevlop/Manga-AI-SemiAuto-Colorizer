"""API routes for pages (F08 integration).

Endpoints:
* POST   /api/v1/pages  — upload a monochrome manga page for a project
* GET    /api/v1/pages/{project_id} — list pages of a project
"""
from __future__ import annotations

import hashlib
import io
import tempfile
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path as PathParam, UploadFile, status
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.create_page import CreatePageInput, CreatePageUseCase
from app.core.config import get_settings
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.infrastructure.database.session import get_session
from app.infrastructure.storage.service import StorageService
from app.modules.page_analysis.repositories import PageRepository
from app.modules.projects.repositories import ProjectRepository

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/pages", tags=["pages"])

ACCEPTED_MIME_TYPES = ["image/png", "image/jpeg", "image/webp"]
MAX_THUMB_SIZE = (400, 400)


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_page(
    project_id: str = Form(...),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Upload a monochrome manga page and register it under a project.

    The file is validated, stored through the storage service, and a
    ``Page`` record is created. Returns the page metadata.
    """
    logger.info("Subiendo página para el proyecto: %s", project_id)
    # Verify project exists.
    project_repo = ProjectRepository(session)
    if not await project_repo.exists(UUID(project_id)):
        logger.warning("Proyecto no encontrado: %s", project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    settings = get_settings()

    # Validate mime type before reading the file.
    if file.content_type not in ACCEPTED_MIME_TYPES:
        logger.warning("Tipo de archivo no permitido: %s", file.content_type)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_file_type",
                "message": "Tipo de archivo no permitido. Use PNG, JPEG o WebP.",
                "accepted": ACCEPTED_MIME_TYPES,
            },
        )

    # Save uploaded file to a temporary location for hashing + storage.
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename or "upload").suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = Path(tmp.name)

        # Validate maximum size.
        if tmp_path.stat().st_size > settings.MAX_UPLOAD_BYTES:
            logger.warning("Archivo excede el tamaño máximo: %s bytes", tmp_path.stat().st_size)
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "code": "file_too_large",
                    "message": f"El archivo excede el tamaño máximo de {settings.MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
                    "max_bytes": settings.MAX_UPLOAD_BYTES,
                },
            )

        storage = StorageService()
        page_repo = PageRepository(session)

        # Compute hash BEFORE storing to disk.
        hash_sha256 = storage.sha256_of_file(tmp_path)

        # Check for duplicate page hash BEFORE persisting to DB.
        existing = await page_repo.get_by_hash(hash_sha256=hash_sha256)
        if existing:
            logger.warning(
                "Hash duplicado detectado: %s — reutilizando página existente",
                hash_sha256,
            )
            # Clean up the duplicate uploaded file since we won't keep it.
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception:
                pass
            return {
                "id": existing.id,
                "project_id": existing.project_id,
                "nombre_archivo_original": existing.nombre_archivo_original,
                "hash_sha256": existing.hash_sha256,
                "ruta_archivo": existing.ruta_archivo,
                "mime_type": existing.mime_type,
                "ancho": existing.ancho,
                "alto": existing.alto,
                "tamano_bytes": existing.tamano_bytes,
                "estado": existing.estado,
                "created_at": existing.created_at,
            }

        # Store the original page image (only if hash is new).
        saved = storage.save(
            source_path=tmp_path,
            artifact_type="originals",
            original_name=file.filename,
        )

        # Create the page record.
        use_case = CreatePageUseCase(project_repo, page_repo)
        page = await use_case.execute(
            CreatePageInput(
                project_id=UUID(project_id),
                nombre_archivo_original=saved["nombre_original"],
                hash_sha256=hash_sha256,
                ruta_archivo=saved["ruta_archivo"],
                mime_type=file.content_type,
                ancho=None,
                alto=None,
                tamano_bytes=saved["tamano_bytes"],
            )
        )

        logger.info(
            "Página subida exitosamente: %s (proyecto: %s)", page.id, project_id
        )

        # Generar y almacenar una miniatura para usar como portada del proyecto (S2).
        thumbnail_url = None
        try:
            with Image.open(saved["ruta_archivo"]) as img:
                img = img.convert("RGB")
                img.thumbnail(MAX_THUMB_SIZE)
                thumb_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                img.save(thumb_tmp, format="JPEG", quality=85)
                thumb_tmp.close()
                preview = storage.save(
                    thumb_tmp.name,
                    artifact_type="previews",
                    original_name=f"thumb_{file.filename}",
                )
                try:
                    Path(thumb_tmp.name).unlink(missing_ok=True)
                except Exception:
                    pass
                thumbnail_url = preview["ruta_archivo"]
                project_repo.update(
                    UUID(project_id), cover_image=thumbnail_url
                )
        except Exception as exc:  # pragma: no cover - thumbnail is best effort
            logger.warning("No se pudo generar la miniatura: %s", exc)

        return {
            "id": page.id,
            "project_id": page.project_id,
            "nombre_archivo_original": page.nombre_archivo_original,
            "hash_sha256": page.hash_sha256,
            "ruta_archivo": page.ruta_archivo,
            "mime_type": page.mime_type,
            "ancho": page.ancho,
            "alto": page.alto,
            "tamano_bytes": page.tamano_bytes,
            "estado": page.estado,
            "created_at": page.created_at,
            "cover_image": thumbnail_url,
        }
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        )
    except Exception as exc:  # pragma: no cover - infra failure path
        logger.exception("Error al subir página: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Failed to upload page.",
        )
    finally:
        try:
            tmp_path.unlink(missing_ok=True)  # type: ignore[name-defined]
        except Exception:  # pragma: no cover - cleanup best effort
            logger.warning("No se pudo limpiar el archivo temporal")


@router.get("/{project_id}")
async def list_pages(
    project_id: str = PathParam(..., description="Project identifier"),
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    """List all pages of a project."""
    try:
        project_repo = ProjectRepository(session)
        if not await project_repo.exists(UUID(project_id)):
            logger.warning("Proyecto no encontrado: %s", project_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found.",
            )

        page_repo = PageRepository(session)
        pages = await page_repo.list(project_id=UUID(project_id))
        return [
            {
                "id": str(p.id),
                "project_id": str(p.project_id),
                "nombre_archivo_original": p.nombre_archivo_original,
                "hash_sha256": p.hash_sha256,
                "ruta_archivo": p.ruta_archivo,
                "mime_type": p.mime_type,
                "ancho": p.ancho,
                "alto": p.alto,
                "tamano_bytes": p.tamano_bytes,
                "estado": p.estado,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in pages
        ]
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - infra failure path
        logger.exception("Error al listar páginas del proyecto %s: %s", project_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al listar páginas.",
        )
"""Endpoints HTTP del Model Registry (prefijo ``/api/v1/models``).

Expone:
* ``GET    /api/v1/models``              — listado (ListModelsUseCase)
* ``GET    /api/v1/models/{model_id}``   — detalle (GetModelUseCase)
* ``POST   /api/v1/models``              — registro local_file / api (RegisterModelUseCase)
* ``PATCH  /api/v1/models/{model_id}/status`` — activar/desactivar (UpdateModelStatusUseCase)
* ``PUT    /api/v1/models/{model_id}``   — editar nombre/descripción/parámetros/credenciales
* ``DELETE /api/v1/models/{model_id}``   — eliminación con protección S19
* ``POST   /api/v1/models/{model_id}/test-connection`` — prueba de conexión API (S16)

Los casos de uso existentes se instancian con el repositorio concreto de
SQLAlchemy; las claves de API se cifran con Fernet (S17) y nunca se devuelven
al frontend (solo enmascaradas).
"""

from __future__ import annotations

import hashlib
from typing import Any
from uuid import UUID

from app.ai_engine.adapters.modelos import resolve_adapter
from app.api.deps import get_current_admin
from app.application.use_cases.get_model import GetModelInput, GetModelUseCase
from app.application.use_cases.list_models import ListModelsInput, ListModelsUseCase
from app.application.use_cases.register_model import RegisterModelInput, RegisterModelUseCase
from app.application.use_cases.update_model_status import (
    UpdateModelStatusInput,
    UpdateModelStatusUseCase,
)
from app.core.config import get_fernet, get_settings
from app.core.exceptions import AppError, ConflictError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.infrastructure.database.session import get_session
from app.infrastructure.storage.service import StorageService
from app.modules.model_registry.repositories import ModelManifestRepository
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/models", tags=["models"])

#: Extensiones de archivo de modelo admitidas (S14).
_ALLOWED_MODEL_EXTENSIONS = frozenset({".pt", ".pth", ".onnx"})

#: Formatos de modelo admitidos.
_ALLOWED_FORMATOS = frozenset({"pt", "onnx", "api"})


# ---------------------------------------------------------------------------
# Helpers de cifrado y enmascaramiento (S17)
# ---------------------------------------------------------------------------


def _mask_api_key(api_key: str | None) -> str | None:
    """Devuelve una versión enmascarada de la clave (ej. ``sk-…abcd``)."""
    if not api_key:
        return None
    visible = api_key[-4:] if len(api_key) >= 4 else api_key
    prefix = api_key[:3] if len(api_key) > 4 else ""
    return f"{prefix}…{visible}" if prefix else f"…{visible}"


def _encrypt_value(plaintext: str | None) -> str | None:
    if plaintext is None:
        return None
    fernet = get_fernet()
    return fernet.encrypt(plaintext.encode()).decode()


def _decrypt_value(ciphertext: str | None) -> str | None:
    if ciphertext is None:
        return None
    fernet = get_fernet()
    return fernet.decrypt(ciphertext.encode()).decode()


# ---------------------------------------------------------------------------
# Helpers de validación de archivo (S14, S15)
# ---------------------------------------------------------------------------


def _validate_uploaded_file(upload_file: UploadFile, max_bytes: int) -> tuple[str, str, str]:
    """Valida extensión, tamaño y checksum de un archivo subido.

    Retorna ``(extension, formato, sha256)``. S15: los archivos .pt se
    cargan con ``weights_only=True`` en el adaptador PyTorch.
    """
    filename = upload_file.filename or ""
    ext = __import__("pathlib").Path(filename).suffix.lower()
    if ext not in _ALLOWED_MODEL_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "extension_not_allowed",
                "message": f"Extensión '{ext}' no permitida. Use uno de {sorted(_ALLOWED_MODEL_EXTENSIONS)}.",
            },
        )

    contenido = upload_file.file.read()
    size = len(contenido)
    upload_file.file.seek(0)
    if size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "code": "file_size_exceeds_limit",
                "message": f"El archivo excede {max_bytes} bytes ({size} bytes recibidos).",
            },
        )

    sha256 = hashlib.sha256(contenido).hexdigest()
    formato = "onnx" if ext == ".onnx" else "pt"
    return ext, formato, sha256


async def _verificar_adaptador_archivo(*, formato: str, ruta_archivo: str, model_id: str) -> None:
    """Verifica que el archivo cargue correctamente mediante el adaptador (S14/S15)."""
    adapter_cls = resolve_adapter(formato)
    adapter = adapter_cls(model_id=model_id, ruta_archivo=ruta_archivo)
    await adapter.validate(resource=ruta_archivo)
    health = await adapter.health_check()
    if not health.get("ok"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "model_load_failed",
                "message": f"El archivo de modelo no carga correctamente: {health.get('detail')}",
            },
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=dict[str, Any])
async def list_models(
    session: AsyncSession = Depends(get_session),
    tarea: str | None = Query(None, description="Filtrar por tarea (familia)"),
    activo: bool | None = Query(None, description="Filtrar solo activos o inactivos"),
    formato: str | None = Query(None, description="Filtrar por formato"),
) -> dict[str, Any]:
    """Lista los manifiestos de modelo registrados."""
    try:
        repo = ModelManifestRepository(session)
        # Usar el caso de uso existente con el repositorio concreto.
        use_case = ListModelsUseCase(model_manifest_repository=repo)
        await use_case.execute(ListModelsInput())
        # to_dict() expone todos los campos de S12 (incluye is_active/formato/salud).
        items = [m.to_dict() for m in await repo.list()]
        # Aplicar filtros ligeros en capa de ruta (los casos de uso no filtran).
        if tarea:

            def normalize_task(value):
                return (value or "").strip().lower().replace("ó", "o")

            requested_task = normalize_task(tarea)
            items = [m for m in items if normalize_task(m["tarea"]) == requested_task]
        if activo is not None:
            items = [m for m in items if m["is_active"] == activo]
        if formato:
            items = [m for m in items if m["formato"] == formato]
        return {"items": items, "total": len(items)}
    except HTTPException:
        raise
    except AppError:
        raise
    except Exception as exc:  # pragma: no cover - infra failure path
        logger.exception("Error al listar modelos: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al listar modelos.",
        )


@router.get("/{model_id}", response_model=dict[str, Any])
async def get_model(
    model_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Devuelve el detalle de un modelo por su ID."""
    try:
        use_case = GetModelUseCase(model_manifest_repository=ModelManifestRepository(session))
        output = await use_case.execute(GetModelInput(model_id=UUID(model_id)))
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found.")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="model_id inválido.")
    except HTTPException:
        raise
    except AppError:
        raise
    except Exception as exc:  # pragma: no cover - infra failure path
        logger.exception("Error al obtener modelo %s: %s", model_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener el modelo.",
        )

    repo = ModelManifestRepository(session)
    manifest = await repo.get(manifest_id=UUID(model_id))
    if manifest is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found.")
    data = manifest.to_dict()
    # Incluir datos del DTO del caso de uso sin exponer secretos.
    data.update(
        {
            "nombre_modelo": output.nombre_modelo,
            "familia": output.familia,
            "version": output.version,
            "estado": output.estado,
            "hash_pesos": output.hash_pesos,
            "licencia": output.licencia,
            "fuente": output.fuente,
            "capacidades": output.capacidades,
            "requisitos_hardware": output.requisitos_hardware,
            "created_at": output.created_at,
            "updated_at": output.updated_at,
        }
    )
    return data


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=dict[str, Any],
    dependencies=[Depends(get_current_admin)],
)
async def register_model(
    session: AsyncSession = Depends(get_session),
    source_type: str = Form(...),
    nombre: str = Form(...),
    familia: str = Form(...),
    version: str = Form(...),
    descripcion: str | None = Form(None),
    licencia: str | None = Form(None),
    # --- solo local_file ---
    file: UploadFile | None = File(None),
    # --- solo api ---
    api_key: str | None = Form(None),
    auth_method: str = Form("bearer"),
    base_url: str | None = Form(None),
    endpoint: str = Form("/infer"),
    modelo: str | None = Form(None),
    timeout: float = Form(30.0),
    retries: int = Form(2),
    is_default: bool = Form(False),
) -> dict[str, Any]:
    """Registra un modelo (archivo local o API externa).

    Para ``source_type=local_file`` se requiere ``file``. Para
    ``source_type=api`` se requieren ``base_url`` y credenciales; se llama a
    ``health_check`` del adaptador API ANTES de guardar (S16).
    """
    settings = get_settings()
    source_type = source_type.strip().lower()
    if source_type not in ("local_file", "api"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_source_type",
                "message": "source_type debe ser 'local_file' o 'api'.",
            },
        )

    capacidades: dict[str, Any] = {
        "descripcion": descripcion,
        "parametros": {},
        "formato": None,
        "salud": "no_verificado",
        "is_default": bool(is_default),
    }
    hash_pesos: str | None = None
    ruta_archivo: str | None = None
    formato: str | None = None

    if source_type == "local_file":
        if file is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "file_required",
                    "message": "Se requiere 'file' para source_type='local_file'.",
                },
            )
        ext, formato, sha256 = _validate_uploaded_file(file, settings.MAX_MODEL_UPLOAD_BYTES)
        hash_pesos = sha256
        capacidades["formato"] = formato
        # Almacenar fuera de la carpeta pública (artifact_type "models") (S14).
        storage = StorageService()
        # Guardar el archivo subido a un temp path para poder hashearlo/copiarlo.
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(file.file.read())
            tmp_path = tmp.name
        try:
            saved = storage.save(
                source_path=tmp_path,
                artifact_type="models",
                original_name=file.filename,
            )
            ruta_archivo = saved["ruta_archivo"]
            hash_pesos = saved["hash_sha256"]
        finally:
            import os

            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        # Verificar que el archivo carga antes de registrar (S14/S15).
        await _verificar_adaptador_archivo(
            formato=formato, ruta_archivo=ruta_archivo, model_id=nombre
        )
        capacidades["salud"] = "ok"
        capacidades["ruta_archivo"] = ruta_archivo

    else:  # api
        if not base_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "base_url_required",
                    "message": "Se requiere 'base_url' para source_type='api'.",
                },
            )
        formato = "api"
        capacidades["formato"] = "api"
        # Prueba de conexión ANTES de guardar (S16).
        adapter_cls = resolve_adapter("api")
        adapter = adapter_cls(
            model_id=nombre,
            base_url=base_url,
            auth_method=auth_method,
            api_key=api_key,
            endpoint=endpoint,
            modelo=modelo,
            timeout=timeout,
            retries=retries,
        )
        health = await adapter.health_check()
        if not health.get("ok"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "connection_test_failed",
                    "message": f"Prueba de conexión fallida: {health.get('detail')}",
                },
            )
        capacidades["salud"] = "ok"
        # Cifrar clave de API (S17).
        _encrypt_value(api_key) if api_key else None

    try:
        use_case = RegisterModelUseCase(model_manifest_repository=ModelManifestRepository(session))
        output = await use_case.execute(
            RegisterModelInput(
                nombre=nombre.strip(),
                familia=familia.strip(),
                version=version.strip(),
                estado="disponible",  # activo por defecto (S18)
                hash_pesos=hash_pesos,
                licencia=licencia,
                fuente=source_type,
                capacidades=capacidades,
                requisitos_hardware={},
            )
        )
    except ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.to_dict(),
        )
    except HTTPException:
        raise
    except AppError:
        raise
    except Exception as exc:  # pragma: no cover - infra failure path
        logger.exception("Error al registrar modelo %s: %s", nombre, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al registrar el modelo.",
        )

    return {
        "id": output.id,
        "nombre": output.nombre_modelo,
        "tarea": output.familia,
        "version": output.version,
        "source_type": source_type,
        "formato": formato,
        "is_active": True,
        "salud": capacidades["salud"],
        "hash_pesos": output.hash_pesos,
        "ruta_archivo": ruta_archivo,
        "api_key": _mask_api_key(api_key),
        "created_at": output.created_at,
        "updated_at": output.updated_at,
    }


@router.patch(
    "/{model_id}/status", response_model=dict[str, Any], dependencies=[Depends(get_current_admin)]
)
async def update_model_status(
    model_id: str,
    session: AsyncSession = Depends(get_session),
    estado: str = Form(..., description="disponible o deshabilitado"),
) -> dict[str, Any]:
    """Activa o desactiva un modelo (S18). Protege modelos en uso (S19)."""
    repo = ModelManifestRepository(session)
    manifest = await repo.get(manifest_id=UUID(model_id))
    if manifest is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found.")

    # S19: impedir desactivar/eliminar si hay jobs en ejecución.
    if estado == "deshabilitado":
        en_uso = await repo.tiene_trabajos_en_ejecucion(manifest_id=UUID(model_id))
        if en_uso:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "model_in_use",
                    "message": "No se puede desactivar el modelo: tiene trabajos de colorización en ejecución.",
                },
            )

    try:
        use_case = UpdateModelStatusUseCase(
            model_manifest_repository=ModelManifestRepository(session)
        )
        output = await use_case.execute(
            UpdateModelStatusInput(model_id=UUID(model_id), estado=estado)
        )
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found.")
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.to_dict())
    except HTTPException:
        raise
    except AppError:
        raise
    except Exception as exc:  # pragma: no cover - infra failure path
        logger.exception("Error al actualizar estado de modelo %s: %s", model_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al actualizar el estado del modelo.",
        )

    return {
        "id": output.id,
        "nombre_modelo": output.nombre_modelo,
        "estado": output.estado,
        "is_active": output.estado == "disponible",
        "updated_at": output.updated_at,
    }


@router.put("/{model_id}", response_model=dict[str, Any], dependencies=[Depends(get_current_admin)])
async def update_model(
    model_id: str,
    session: AsyncSession = Depends(get_session),
    nombre: str | None = Form(None),
    descripcion: str | None = Form(None),
    # credenciales (solo api)
    api_key: str | None = Form(None),
    auth_method: str | None = Form(None),
    base_url: str | None = Form(None),
    endpoint: str | None = Form(None),
    modelo: str | None = Form(None),
    timeout: float | None = Form(None),
    retries: int | None = Form(None),
    is_default: bool | None = Form(None),
) -> dict[str, Any]:
    """Edita nombre, descripción, parámetros y credenciales.

    Si cambia la clave de API, se regenera el cifrado (S17).
    """
    repo = ModelManifestRepository(session)
    manifest = await repo.get(manifest_id=UUID(model_id))
    if manifest is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found.")

    capacidades = dict(manifest.capacidades or {})
    if nombre is not None:
        manifest.nombre_modelo = nombre.strip()
    if descripcion is not None:
        capacidades["descripcion"] = descripcion
    if is_default is not None:
        capacidades["is_default"] = bool(is_default)

    parametros_soportados = dict(manifest.parametros_soportados or {})
    if api_key is not None:
        parametros_soportados["api_key_enc"] = _encrypt_value(api_key)
    if auth_method is not None:
        parametros_soportados["auth_method"] = auth_method
    if base_url is not None:
        parametros_soportados["base_url"] = base_url
    if endpoint is not None:
        parametros_soportados["endpoint"] = endpoint
    if modelo is not None:
        parametros_soportados["modelo"] = modelo
    if timeout is not None:
        parametros_soportados["timeout"] = timeout
    if retries is not None:
        parametros_soportados["retries"] = retries

    try:
        updated = await repo.update(
            manifest_id=UUID(model_id),
            nombre_modelo=manifest.nombre_modelo,
            capacidades=capacidades,
            parametros_soportados=parametros_soportados,
        )
    except AppError:
        raise
    except Exception as exc:  # pragma: no cover - infra failure path
        logger.exception("Error al editar modelo %s: %s", model_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al editar el modelo.",
        )
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found.")

    return {
        "id": str(updated.id),
        "nombre": updated.nombre_modelo,
        "descripcion": updated.descripcion,
        "is_default": updated.is_default,
        "api_key": _mask_api_key(_decrypt_value(updated.api_key_enc)),
        "parametros_soportados": {
            k: v for k, v in (updated.parametros_soportados or {}).items() if k != "api_key_enc"
        },
        "updated_at": updated.updated_at.isoformat() if updated.updated_at else None,
    }


@router.delete("/{model_id}", dependencies=[Depends(get_current_admin)])
async def delete_model(
    model_id: str,
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Elimina un modelo. Protege modelos en uso (S19)."""
    repo = ModelManifestRepository(session)
    manifest = await repo.get(manifest_id=UUID(model_id))
    if manifest is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found.")

    # S19: impedir eliminar si hay jobs en ejecución.
    en_uso = await repo.tiene_trabajos_en_ejecucion(manifest_id=UUID(model_id))
    if en_uso:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "model_in_use",
                "message": "No se puede eliminar el modelo: tiene trabajos de colorización en ejecución.",
            },
        )

    # Eliminar archivo de almacenamiento asociado si existe.
    try:
        storage = StorageService()
        storage.delete(str(manifest.id), "models")
    except Exception:
        # No bloquear la eliminación por fallo de storage.
        logger.warning("No se pudo eliminar el artefacto de almacenamiento del modelo %s", model_id)

    deleted = await repo.delete(manifest_id=UUID(model_id))
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{model_id}/test-connection",
    response_model=dict[str, Any],
    dependencies=[Depends(get_current_admin)],
)
async def test_connection(
    model_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Prueba de conexión para modelos API (S16)."""
    repo = ModelManifestRepository(session)
    manifest = await repo.get(manifest_id=UUID(model_id))
    if manifest is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found.")
    if manifest.source_type != "api":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "not_api_model",
                "message": "test-connection solo aplica a modelos de tipo 'api'.",
            },
        )

    ps = manifest.parametros_soportados or {}
    api_key = _decrypt_value(ps.get("api_key_enc"))
    adapter_cls = resolve_adapter("api")
    adapter = adapter_cls(
        model_id=manifest.nombre_modelo,
        base_url=ps.get("base_url", ""),
        auth_method=ps.get("auth_method", "bearer"),
        api_key=api_key,
        endpoint=ps.get("endpoint", "/infer"),
        modelo=ps.get("modelo"),
        timeout=float(ps.get("timeout", 30.0)),
        retries=int(ps.get("retries", 2)),
    )
    health = await adapter.health_check()
    return {
        "model_id": str(manifest.id),
        "ok": bool(health.get("ok")),
        "detail": health.get("detail", ""),
    }

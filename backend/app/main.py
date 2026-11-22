"""Punto de entrada de la aplicación FastAPI SUMI.

Configura el logging estructurado, incluye todos los routers de la API y
expone el endpoint de health check. Toda inicialización está protegida con
try/except para fail-fast con diagnóstico claro.
"""

from __future__ import annotations

import os
import uuid
from contextlib import asynccontextmanager

from app.api.deps import get_current_user
from app.api.routes.analysis import router as analysis_router
from app.api.routes.auth import router as auth_router
from app.api.routes.characters import router as characters_router
from app.api.routes.colorizations import router as colorizations_router
from app.api.routes.masks import router as masks_router
from app.api.routes.metrics import router as metrics_router
from app.api.routes.models import router as models_router
from app.api.routes.pages import router as pages_router
from app.api.routes.projects import router as projects_router
from app.core.config import get_settings
from app.core.exceptions import (
    AppError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from app.core.logging import get_logger
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = get_logger(__name__)


async def _bootstrap_first_admin() -> None:
    """Crea el primer administrador si FIRST_ADMIN_* está definido y no hay usuarios."""
    settings = get_settings()
    if not (settings.FIRST_ADMIN_EMAIL and settings.FIRST_ADMIN_PASSWORD):
        return
    from app.core.security import get_password_hash
    from app.infrastructure.database.session import async_session_factory
    from app.modules.users.repositories import UserRepository

    async with async_session_factory() as session:
        repo = UserRepository(session)
        if await repo.count() == 0:
            await repo.create(
                email=settings.FIRST_ADMIN_EMAIL,
                hashed_password=get_password_hash(settings.FIRST_ADMIN_PASSWORD),
                is_admin=True,
            )
            logger.info("Administrador inicial creado: %s", settings.FIRST_ADMIN_EMAIL)


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        await _bootstrap_first_admin()
    except Exception as exc:  # no impedir el arranque si la BD aún no migró
        logger.error("No se pudo crear el administrador inicial: %s", exc)
    yield


app = FastAPI(title="Manga Colorizer API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in get_settings().CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID", "Retry-After"],
)

# Miniaturas públicas (solo previews; originales y artefactos no se exponen).
_previews = os.path.join(os.environ.get("STORAGE_ROOT", "./data"), "previews")
os.makedirs(_previews, exist_ok=True)
app.mount("/files/previews", StaticFiles(directory=_previews), name="previews")

# Seguridad por defecto: todo router de negocio exige un usuario autenticado.
# Solo /health y /api/v1/auth/* (login) son públicos.
_protected = [Depends(get_current_user)]

try:
    app.include_router(auth_router)
    app.include_router(projects_router, dependencies=_protected)
    app.include_router(pages_router, dependencies=_protected)
    app.include_router(analysis_router, dependencies=_protected)
    app.include_router(colorizations_router, dependencies=_protected)
    app.include_router(characters_router, dependencies=_protected)
    app.include_router(masks_router, dependencies=_protected)
    app.include_router(metrics_router, dependencies=_protected)
    app.include_router(models_router, dependencies=_protected)
    logger.info("Todos los routers de la API registrados correctamente")
except Exception as exc:  # pragma: no cover - fail-fast guard
    logger.exception("Error al registrar routers de la API: %s", exc)
    raise


@app.get("/health")
def health() -> dict[str, str]:
    """Health check del servicio."""
    try:
        return {"status": "ok"}
    except Exception as exc:  # pragma: no cover - health check should not fail
        logger.exception("Error en health check: %s", exc)
        return {"status": "error", "detail": str(exc)}


# --- Manejo global de errores: siempre devuelve el envelope
# {code, message, details, request_id} que espera el frontend. ---
_STATUS = {
    NotFoundError: 404,
    ValidationError: 422,
    ConflictError: 409,
    UnauthorizedError: 401,
    ForbiddenError: 403,
}


def _envelope(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details=None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex
    return JSONResponse(
        status_code=status_code,
        content={"code": code, "message": message, "details": details, "request_id": rid},
        headers={**(headers or {}), "X-Request-ID": rid},
    )


@app.exception_handler(AppError)
async def _app_error(request: Request, exc: AppError) -> JSONResponse:
    status_code = next((s for c, s in _STATUS.items() if isinstance(exc, c)), 500)
    return _envelope(request, status_code, exc.code, exc.message, exc.details)


@app.exception_handler(StarletteHTTPException)
async def _http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    d = exc.detail
    hdrs = dict(exc.headers) if getattr(exc, "headers", None) else None
    if isinstance(d, dict):
        return _envelope(
            request,
            exc.status_code,
            str(d.get("code", "http_error")),
            str(d.get("message", d)),
            d.get("details"),
            hdrs,
        )
    return _envelope(request, exc.status_code, "http_error", str(d), None, hdrs)


@app.exception_handler(RequestValidationError)
async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    return _envelope(
        request, 422, "validation_error", "Solicitud inválida", {"errors": jsonable_errors(exc)}
    )


def jsonable_errors(exc: RequestValidationError) -> list:
    return [
        {"loc": list(e.get("loc", [])), "msg": e.get("msg"), "type": e.get("type")}
        for e in exc.errors()
    ]


@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Error no controlado en %s %s: %s", request.method, request.url.path, exc)
    return _envelope(request, 500, "internal_error", "Error interno del servidor")

"""Punto de entrada de la aplicación FastAPI SUMI.

Configura el logging estructurado, incluye todos los routers de la API y
expone el endpoint de health check. Toda inicialización está protegida con
try/except para fail-fast con diagnóstico claro.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.analysis import router as analysis_router
from app.api.routes.colorizations import router as colorizations_router
from app.api.routes.metrics import router as metrics_router
from app.api.routes.pages import router as pages_router
from app.api.routes.projects import router as projects_router
from app.core.logging import get_logger

logger = get_logger(__name__)

app = FastAPI(title="Manga Colorizer API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    app.include_router(projects_router)
    app.include_router(pages_router)
    app.include_router(analysis_router)
    app.include_router(colorizations_router)
    app.include_router(metrics_router)
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

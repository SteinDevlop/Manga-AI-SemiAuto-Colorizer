"""SQLAlchemy domain model for the model manifest registry.

Defines ``ModelManifest``, mapped to the ``model_manifests`` table, which
catalogs AI models available for manga colorization: name, family, version,
weights hash, license, source, capabilities, hardware requirements, status,
and supported parameters.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class ModelManifest(Base):
    """Manifest of an AI model used for manga colorization.

    Table ``model_manifests``. Inherits ``id`` (UUID primary key),
    ``created_at`` and ``updated_at`` (UTC timestamps) from ``Base``.
    """

    __tablename__ = "model_manifests"

    nombre_modelo: Mapped[str] = mapped_column(String(255), nullable=False)
    familia: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(100), nullable=False)
    hash_pesos: Mapped[str | None] = mapped_column(String(128), nullable=True)
    licencia: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fuente: Mapped[str | None] = mapped_column(String(512), nullable=True)
    capacidades: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    requisitos_hardware: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    estado: Mapped[str] = mapped_column(String(50), nullable=False, default="disponible")
    parametros_soportados: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

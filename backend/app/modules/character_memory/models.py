"""SQLAlchemy domain model for the model manifest registry.

Defines ``ModelManifest``, mapped to the ``model_manifests`` table, which
catalogs AI models available for manga colorization: name, family, version,
weights hash, license, source, capabilities, hardware requirements, status,
and supported parameters.
"""

from __future__ import annotations

import uuid
from typing import Any

from app.infrastructure.database.base import Base
from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


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


class CharacterMemory(Base):
    """Memoria estable de un personaje entre páginas y viñetas.

    Table ``character_memory``. Almacena embeddings y referencias estables
    para reproducir la consistencia cromática y de identidad a lo largo del
    manga. No almacena imágenes binarias.
    """

    __tablename__ = "character_memory"

    character_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("characters.id"),
        nullable=False,
        index=True,
    )
    embedding: Mapped[str | None] = mapped_column(String, nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    atributos_estables: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    atributos_escena: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    referencia_estable: Mapped[str | None] = mapped_column(String(512), nullable=True)
    pagina_origen_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("pages.id"),
        nullable=True,
        index=True,
    )

    character: Mapped["Character"] = relationship("Character")

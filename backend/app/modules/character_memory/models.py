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

# ModelManifest vive en app.modules.model_registry (única definición de la
# tabla ``model_manifests``); se re-exporta aquí por compatibilidad.
from app.modules.model_registry.models import ModelManifest  # noqa: E402,F401
from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


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

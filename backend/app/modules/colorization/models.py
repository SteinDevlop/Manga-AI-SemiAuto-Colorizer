"""Colorization domain models.

Defines ``MaskArtifact`` and ``ColorizationJob`` SQLAlchemy 2.0 entities.
Both inherit ``id`` (UUID PK), ``created_at`` and ``updated_at`` (UTC) from
the shared declarative base, and store only metadata and file paths -- no
binary image content.
"""

import uuid
from typing import Optional

from sqlalchemy import ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base


class MaskArtifact(Base):
    """Mask artifact produced for a character appearance.

    References ``character_appearances`` through a non-nullable, indexed
    foreign key. Stores mask metadata and a storage path only.
    """

    __tablename__ = "mask_artifacts"

    appearance_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("character_appearances.id"),
        nullable=False,
        index=True,
    )
    tipo_mascara: Mapped[str] = mapped_column(String, nullable=False)
    ruta_archivo: Mapped[str] = mapped_column(String, nullable=False)
    hash_sha256: Mapped[str] = mapped_column(String, nullable=False)
    ancho: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    alto: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    appearance: Mapped["CharacterAppearance"] = relationship("CharacterAppearance")


class ColorizationJob(Base):
    """Colorization job tracking the state of an analysis result.

    References ``analyses`` through a non-nullable, indexed foreign key.
    Stores job state, progress and optional output metadata -- no binary
    images.
    """

    __tablename__ = "colorization_jobs"

    analysis_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("analyses.id"),
        nullable=False,
        index=True,
    )
    estado: Mapped[str] = mapped_column(String, default="pending", nullable=False)
    progreso: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mensaje: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ruta_resultado: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    version_modelo: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    parametros: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    analysis: Mapped["Analysis"] = relationship("Analysis")

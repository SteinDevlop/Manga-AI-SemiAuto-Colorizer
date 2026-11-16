"""Asset domain models.

Defines the ``Artifact`` SQLAlchemy 2.0 entity tracking stored files
(originals, masks, references, previews, results). Only metadata and
filesystem paths are stored in PostgreSQL -- no binary image content.
"""

from __future__ import annotations

import uuid

from app.infrastructure.database.base import Base
from sqlalchemy import BigInteger, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Artifact(Base):
    """A stored file artifact linked to a page and/or a colorization job.

    ``artifact_id`` is the stable public identifier; client-provided paths
    are never used as identifiers. Binary content lives on disk through the
    storage service -- only metadata and paths are persisted here.
    """

    __tablename__ = "artifacts"

    artifact_id: Mapped[str] = mapped_column(
        String, nullable=False, unique=True, index=True
    )
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    nombre_original: Mapped[str | None] = mapped_column(String, nullable=True)
    ruta_archivo: Mapped[str] = mapped_column(String, nullable=False)
    hash_sha256: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    tamano_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String, nullable=True)
    pagina_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("pages.id", ondelete="SET NULL"), nullable=True, index=True
    )
    trabajo_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("colorization_jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    page: Mapped["Page"] = relationship("Page")
    job: Mapped["ColorizationJob"] = relationship("ColorizationJob")

"""SQLAlchemy 2.0 domain models for projects and pages.

Defines ``Project`` and ``Page`` entities, inheriting the common UUID
primary key and UTC ``created_at``/``updated_at`` columns from
``app.infrastructure.database.base.Base``. Only file metadata and paths
are stored -- no binary image content is kept in the database.
"""

from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base


class Project(Base):
    """A manga colorization project.

    A project owns many pages. Deleting a project cascades the deletion
    to all of its pages.
    """

    __tablename__ = "projects"

    nombre: Mapped[str] = mapped_column(String, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)

    pages: Mapped[list["Page"]] = relationship(
        "Page",
        back_populates="project",
        cascade="all, delete-orphan",
    )


class Page(Base):
    """A single manga page belonging to a project.

    Stores only metadata and a filesystem path. A page belongs to one
    project and owns many panels and analyses; deleting the page
    cascades to both collections.
    """

    __tablename__ = "pages"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nombre_archivo_original: Mapped[str] = mapped_column(String, nullable=False)
    hash_sha256: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    ruta_archivo: Mapped[str] = mapped_column(String, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String, nullable=True)
    ancho: Mapped[int | None] = mapped_column(Integer, nullable=True)
    alto: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tamano_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    estado: Mapped[str] = mapped_column(String, nullable=False, default="uploaded")

    project: Mapped["Project"] = relationship("Project", back_populates="pages")
    panels: Mapped[list["Panel"]] = relationship(
        "Panel",
        back_populates="page",
        cascade="all, delete-orphan",
    )
    analyses: Mapped[list["Analysis"]] = relationship(
        "Analysis",
        back_populates="page",
        cascade="all, delete-orphan",
    )

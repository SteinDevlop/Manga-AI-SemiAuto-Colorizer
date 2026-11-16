"""Domain models Panel and Analysis for the page analysis module.

Defines the SQLAlchemy 2.0 ``Panel`` and ``Analysis`` entities together with
their relationships to ``Page``. This module contains data models only; no
computer vision logic is implemented here.
"""

from typing import TYPE_CHECKING

import uuid

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from app.modules.projects.models import Page


class Panel(Base):
    """A panel detected within a comic page."""

    __tablename__ = "panels"

    page_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pages.id"),
        nullable=False,
        index=True,
    )
    numero_orden: Mapped[int] = mapped_column(Integer, nullable=False)
    x: Mapped[float] = mapped_column(Float, nullable=False)
    y: Mapped[float] = mapped_column(Float, nullable=False)
    ancho: Mapped[float] = mapped_column(Float, nullable=False)
    alto: Mapped[float] = mapped_column(Float, nullable=False)
    confianza_deteccion: Mapped[float | None] = mapped_column(Float, nullable=True)

    page: Mapped["Page"] = relationship("Page", foreign_keys=[page_id])


class Analysis(Base):
    """The analysis result of a comic page."""

    __tablename__ = "analyses"

    page_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pages.id"),
        nullable=False,
        index=True,
        unique=True,
    )
    estado: Mapped[str] = mapped_column(
        String,
        default="analysis_pending",
        nullable=False,
    )
    confianza_global: Mapped[float | None] = mapped_column(Float, nullable=True)
    version_modelo: Mapped[str | None] = mapped_column(String, nullable=True)

    page: Mapped["Page"] = relationship("Page", foreign_keys=[page_id])

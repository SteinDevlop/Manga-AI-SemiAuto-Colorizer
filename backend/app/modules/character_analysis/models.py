"""SQLAlchemy 2.0 domain models for character analysis.

Defines the ``Character`` and ``CharacterAppearance`` entities. Identity
matching logic is intentionally not implemented here; this module only
defines the data models and their relationships.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base


class Character(Base):
    """A detected or registered manga character.

    Attributes:
        id: Primary key UUID (inherited from ``Base``).
        nombre: Character name. Not nullable.
        descripcion: Optional free-text description.
        confianza_identidad: Optional identity confidence score.
        created_at/updated_at: UTC timestamps (inherited from ``Base``).
        appearances: One-to-many relationship with ``CharacterAppearance``.
    """

    __tablename__ = "characters"

    nombre: Mapped[str] = mapped_column(String, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    confianza_identidad: Mapped[float | None] = mapped_column(Float, nullable=True)

    appearances: Mapped[list["CharacterAppearance"]] = relationship(
        "CharacterAppearance",
        back_populates="character",
        cascade="all, delete-orphan",
    )


class CharacterAppearance(Base):
    """A single appearance of a character on a page or panel.

    Attributes:
        id: Primary key UUID (inherited from ``Base``).
        page_id: Foreign key to ``pages.id``. Not nullable, indexed.
        character_id: Foreign key to ``characters.id``. Not nullable, indexed.
        panel_id: Optional foreign key to ``panels.id``. Indexed.
        confianza_deteccion: Optional detection confidence score.
        created_at/updated_at: UTC timestamps (inherited from ``Base``).
        page: Many-to-one relationship with ``Page``.
        character: Many-to-one relationship with ``Character``.
        panel: Optional many-to-one relationship with ``Panel``.
    """

    __tablename__ = "character_appearances"

    page_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    character_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    panel_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("panels.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    confianza_deteccion: Mapped[float | None] = mapped_column(Float, nullable=True)

    page: Mapped["Page"] = relationship("Page")
    character: Mapped["Character"] = relationship("Character", back_populates="appearances")
    panel: Mapped["Panel | None"] = relationship("Panel")

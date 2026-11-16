"""Domain models for character configuration.

Defines ``CharacterAttribute`` and ``CharacterPalette``, both many-to-one
children of ``Character``. All stored values are editable suggestions; no
official colors are invented here.
"""

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base


class CharacterAttribute(Base):
    """An attribute of a character (e.g. hair, eyes, skin) with a suggested
    and an approved value."""

    __tablename__ = "character_attributes"

    character_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("characters.id"),
        nullable=False,
        index=True,
    )
    nombre_atributo: Mapped[str] = mapped_column(String, nullable=False)
    valor_sugerido: Mapped[str | None] = mapped_column(String, nullable=True)
    valor_aprobado: Mapped[str | None] = mapped_column(String, nullable=True)
    esta_aprobado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confianza_sugerencia: Mapped[float | None] = mapped_column(Float, nullable=True)

    character: Mapped["Character"] = relationship("Character")


class CharacterPalette(Base):
    """A color entry of a character palette (e.g. base color, shadow, light)."""

    __tablename__ = "character_palettes"

    character_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("characters.id"),
        nullable=False,
        index=True,
    )
    nombre_color: Mapped[str] = mapped_column(String, nullable=False)
    valor_hex: Mapped[str | None] = mapped_column(String, nullable=True)
    esta_aprobado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    character: Mapped["Character"] = relationship("Character")

"""Base CRUD repositories for the character configuration domain entities.

Defines repositories for ``CharacterAttribute`` and ``CharacterPalette``. All
operations are async and backed by an injected SQLAlchemy async session.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.modules.character_configuration.models import (
    CharacterAttribute,
    CharacterPalette,
)
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession


class CharacterAttributeRepository:
    """Repository for ``CharacterAttribute`` entities.

    An attribute belongs to one character. Listings can be filtered by
    character id.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, attribute_id: UUID) -> CharacterAttribute | None:
        """Return the attribute with the given id, or ``None`` if missing."""
        stmt: Select = select(CharacterAttribute).where(CharacterAttribute.id == attribute_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, character_id: UUID | None = None) -> list[CharacterAttribute]:
        """Return attributes, optionally filtered by character id."""
        stmt: Select = select(CharacterAttribute).order_by(CharacterAttribute.created_at)
        if character_id is not None:
            stmt = stmt.where(CharacterAttribute.character_id == character_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_character_and_name(
        self, *, character_id: UUID, nombre_atributo: str
    ) -> CharacterAttribute | None:
        stmt = select(CharacterAttribute).where(
            CharacterAttribute.character_id == character_id,
            CharacterAttribute.nombre_atributo == nombre_atributo,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, **kwargs: Any) -> CharacterAttribute:
        """Create and persist a new attribute from the given attributes."""
        attribute = CharacterAttribute(**kwargs)
        self.session.add(attribute)
        await self.session.commit()
        await self.session.refresh(attribute)
        return attribute

    async def update(self, attribute_id: UUID, **kwargs: Any) -> CharacterAttribute | None:
        """Update the attributes of the attribute with the given id."""
        attribute = await self.get(attribute_id)
        if attribute is None:
            return None
        for key, value in kwargs.items():
            setattr(attribute, key, value)
        await self.session.commit()
        await self.session.refresh(attribute)
        return attribute

    async def delete(self, attribute_id: UUID) -> bool:
        """Delete the attribute with the given id. Returns ``False`` if absent."""
        attribute = await self.get(attribute_id)
        if attribute is None:
            return False
        await self.session.delete(attribute)
        await self.session.commit()
        return True

    async def exists(self, attribute_id: UUID) -> bool:
        """Return ``True`` when an attribute with the given id exists."""
        stmt: Select = (
            select(CharacterAttribute.id).where(CharacterAttribute.id == attribute_id).limit(1)
        )
        result = await self.session.execute(stmt)
        return result.first() is not None


class CharacterPaletteRepository:
    """Repository for ``CharacterPalette`` entities.

    A palette entry belongs to one character. Listings can be filtered by
    character id.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, palette_id: UUID) -> CharacterPalette | None:
        """Return the palette entry with the given id, or ``None`` if missing."""
        stmt: Select = select(CharacterPalette).where(CharacterPalette.id == palette_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, character_id: UUID | None = None) -> list[CharacterPalette]:
        """Return palette entries, optionally filtered by character id."""
        stmt: Select = select(CharacterPalette).order_by(CharacterPalette.created_at)
        if character_id is not None:
            stmt = stmt.where(CharacterPalette.character_id == character_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_character_and_name(
        self, *, character_id: UUID, nombre_color: str
    ) -> CharacterPalette | None:
        stmt = select(CharacterPalette).where(
            CharacterPalette.character_id == character_id,
            CharacterPalette.nombre_color == nombre_color,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, **kwargs: Any) -> CharacterPalette:
        """Create and persist a new palette entry from the given attributes."""
        palette = CharacterPalette(**kwargs)
        self.session.add(palette)
        await self.session.commit()
        await self.session.refresh(palette)
        return palette

    async def update(self, palette_id: UUID, **kwargs: Any) -> CharacterPalette | None:
        """Update the attributes of the palette entry with the given id."""
        palette = await self.get(palette_id)
        if palette is None:
            return None
        for key, value in kwargs.items():
            setattr(palette, key, value)
        await self.session.commit()
        await self.session.refresh(palette)
        return palette

    async def delete(self, palette_id: UUID) -> bool:
        """Delete the palette entry with the given id. Returns ``False`` if absent."""
        palette = await self.get(palette_id)
        if palette is None:
            return False
        await self.session.delete(palette)
        await self.session.commit()
        return True

    async def exists(self, palette_id: UUID) -> bool:
        """Return ``True`` when a palette entry with the given id exists."""
        stmt: Select = select(CharacterPalette.id).where(CharacterPalette.id == palette_id).limit(1)
        result = await self.session.execute(stmt)
        return result.first() is not None

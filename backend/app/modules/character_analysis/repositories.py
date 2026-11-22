"""Base CRUD repositories for the character analysis domain entities.

Defines repositories for ``Character`` and ``CharacterAppearance``. All
operations are async and backed by an injected SQLAlchemy async session.
Identity matching logic is intentionally not implemented here; this module only
provides data access.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.modules.character_analysis.models import Character, CharacterAppearance
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class CharacterRepository:
    """Repository for ``Character`` entities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, character_id: UUID) -> Character | None:
        """Return the character with the given id, or ``None`` if missing."""
        stmt: Select = select(Character).where(Character.id == character_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self) -> list[Character]:
        """Return all characters ordered by creation time."""
        stmt: Select = select(Character).order_by(Character.created_at)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, **kwargs: Any) -> Character:
        """Create and persist a new character from the given attributes."""
        character = Character(**kwargs)
        self.session.add(character)
        await self.session.commit()
        await self.session.refresh(character)
        return character

    async def update(self, character_id: UUID, **kwargs: Any) -> Character | None:
        """Update the attributes of the character with the given id."""
        character = await self.get(character_id)
        if character is None:
            return None
        for key, value in kwargs.items():
            setattr(character, key, value)
        await self.session.commit()
        await self.session.refresh(character)
        return character

    async def delete(self, character_id: UUID) -> bool:
        """Delete the character with the given id. Returns ``False`` if absent."""
        character = await self.get(character_id)
        if character is None:
            return False
        await self.session.delete(character)
        await self.session.commit()
        return True

    async def exists(self, character_id: UUID) -> bool:
        """Return ``True`` when a character with the given id exists."""
        stmt: Select = select(Character.id).where(Character.id == character_id).limit(1)
        result = await self.session.execute(stmt)
        return result.first() is not None


class CharacterAppearanceRepository:
    """Repository for ``CharacterAppearance`` entities.

    An appearance references one page and one character, and optionally one
    panel. Listings can be filtered by page id and/or character id.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, appearance_id: UUID) -> CharacterAppearance | None:
        """Return the appearance with the given id, or ``None`` if missing."""
        stmt: Select = select(CharacterAppearance).where(CharacterAppearance.id == appearance_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        page_id: UUID | None = None,
        character_id: UUID | None = None,
    ) -> list[CharacterAppearance]:
        """Return appearances, optionally filtered by page id and/or character id."""
        stmt: Select = select(CharacterAppearance).order_by(CharacterAppearance.created_at)
        if page_id is not None:
            stmt = stmt.where(CharacterAppearance.page_id == page_id)
        if character_id is not None:
            stmt = stmt.where(CharacterAppearance.character_id == character_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_by_page(self, *, page_id: UUID) -> list[CharacterAppearance]:
        return await self.list(page_id=page_id)

    async def list_by_character(self, *, character_id: UUID) -> list[CharacterAppearance]:
        stmt: Select = (
            select(CharacterAppearance)
            .options(selectinload(CharacterAppearance.page), selectinload(CharacterAppearance.panel))
            .where(CharacterAppearance.character_id == character_id)
            .order_by(CharacterAppearance.created_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_character(
        self, *, appearance_id: UUID, character_id: UUID
    ) -> CharacterAppearance | None:
        return await self.update(appearance_id, character_id=character_id)

    async def create(self, **kwargs: Any) -> CharacterAppearance:
        """Create and persist a new appearance from the given attributes."""
        appearance = CharacterAppearance(**kwargs)
        self.session.add(appearance)
        await self.session.commit()
        await self.session.refresh(appearance)
        return appearance

    async def update(self, appearance_id: UUID, **kwargs: Any) -> CharacterAppearance | None:
        """Update the attributes of the appearance with the given id."""
        appearance = await self.get(appearance_id)
        if appearance is None:
            return None
        for key, value in kwargs.items():
            setattr(appearance, key, value)
        await self.session.commit()
        await self.session.refresh(appearance)
        return appearance

    async def delete(self, appearance_id: UUID) -> bool:
        """Delete the appearance with the given id. Returns ``False`` if absent."""
        appearance = await self.get(appearance_id)
        if appearance is None:
            return False
        await self.session.delete(appearance)
        await self.session.commit()
        return True

    async def exists(self, appearance_id: UUID) -> bool:
        """Return ``True`` when an appearance with the given id exists."""
        stmt: Select = (
            select(CharacterAppearance.id).where(CharacterAppearance.id == appearance_id).limit(1)
        )
        result = await self.session.execute(stmt)
        return result.first() is not None

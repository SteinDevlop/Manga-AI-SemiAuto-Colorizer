"""Base CRUD repository for the ``ModelManifest`` entity.

Provides ``get``, ``list``, ``create``, ``update``, ``delete`` and ``exists``
operations backed by an injected SQLAlchemy async session.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.character_memory.models import ModelManifest


class ModelManifestRepository:
    """Repository for ``ModelManifest`` entries.

    Catalogs AI models available for manga colorization. Lookups are performed
    by UUID primary key.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, manifest_id: UUID) -> ModelManifest | None:
        """Return the manifest with the given id, or ``None`` if missing."""
        stmt: Select = select(ModelManifest).where(ModelManifest.id == manifest_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self) -> list[ModelManifest]:
        """Return all manifests ordered by creation time."""
        stmt: Select = select(ModelManifest).order_by(ModelManifest.created_at)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, **kwargs: Any) -> ModelManifest:
        """Create and persist a new manifest from the given attributes."""
        manifest = ModelManifest(**kwargs)
        self.session.add(manifest)
        await self.session.commit()
        await self.session.refresh(manifest)
        return manifest

    async def update(self, manifest_id: UUID, **kwargs: Any) -> ModelManifest | None:
        """Update the attributes of the manifest with the given id."""
        manifest = await self.get(manifest_id)
        if manifest is None:
            return None
        for key, value in kwargs.items():
            setattr(manifest, key, value)
        await self.session.commit()
        await self.session.refresh(manifest)
        return manifest

    async def delete(self, manifest_id: UUID) -> bool:
        """Delete the manifest with the given id. Returns ``False`` if absent."""
        manifest = await self.get(manifest_id)
        if manifest is None:
            return False
        await self.session.delete(manifest)
        await self.session.commit()
        return True

    async def exists(self, manifest_id: UUID) -> bool:
        """Return ``True`` when a manifest with the given id exists."""
        stmt: Select = (
            select(ModelManifest.id).where(ModelManifest.id == manifest_id).limit(1)
        )
        result = await self.session.execute(stmt)
        return result.first() is not None

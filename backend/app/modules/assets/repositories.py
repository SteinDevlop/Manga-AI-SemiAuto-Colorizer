"""Artifact repository.

Data-access layer for the ``Artifact`` entity using SQLAlchemy 2.0 async
sessions. Every method is async and stores only metadata and file paths --
no binary image content.
"""

from __future__ import annotations

import uuid
from typing import Any

import sqlalchemy as sa
from app.modules.assets.models import Artifact
from sqlalchemy.ext.asyncio import AsyncSession


class ArtifactRepository:
    """Repository for ``Artifact`` entities.

    Args:
        session: SQLAlchemy async session used for all database operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, artifact_id: str) -> Artifact | None:
        """Return the artifact with the public ``artifact_id``, or None."""
        stmt = sa.select(Artifact).where(Artifact.artifact_id == artifact_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, filtros: dict[str, Any] | None = None) -> list[Artifact]:
        """Return all artifacts, optionally filtered by column equality."""
        stmt = sa.select(Artifact)
        if filtros:
            for column_name, value in filtros.items():
                stmt = stmt.where(getattr(Artifact, column_name) == value)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> Artifact:
        """Create and persist a new artifact, returning the refreshed instance."""
        artifact = Artifact(**kwargs)
        self.session.add(artifact)
        await self.session.commit()
        await self.session.refresh(artifact)
        return artifact

    async def update(self, artifact_id: str, **kwargs: Any) -> Artifact | None:
        """Update fields of the artifact identified by ``artifact_id``."""
        stmt = sa.select(Artifact).where(Artifact.artifact_id == artifact_id)
        result = await self.session.execute(stmt)
        artifact = result.scalar_one_or_none()
        if artifact is None:
            return None
        for key, value in kwargs.items():
            setattr(artifact, key, value)
        await self.session.commit()
        await self.session.refresh(artifact)
        return artifact

    async def delete(self, artifact_id: str) -> bool:
        """Delete the artifact identified by ``artifact_id``."""
        stmt = sa.select(Artifact).where(Artifact.artifact_id == artifact_id)
        result = await self.session.execute(stmt)
        artifact = result.scalar_one_or_none()
        if artifact is None:
            return False
        await self.session.delete(artifact)
        await self.session.commit()
        return True

    async def exists(self, artifact_id: str) -> bool:
        """Return True if an artifact with the given public id exists."""
        stmt = sa.select(Artifact.id).where(Artifact.artifact_id == artifact_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def exists_by_hash(self, hash_sha256: str) -> bool:
        """Return True if an artifact with the given SHA-256 hash exists."""
        stmt = sa.select(Artifact.id).where(Artifact.hash_sha256 == hash_sha256)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def list_by_page(self, page_id: uuid.UUID) -> list[Artifact]:
        """Return all artifacts linked to the given page."""
        stmt = sa.select(Artifact).where(Artifact.pagina_id == page_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_job(self, job_id: uuid.UUID) -> list[Artifact]:
        """Return all artifacts linked to the given colorization job."""
        stmt = sa.select(Artifact).where(Artifact.trabajo_id == job_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

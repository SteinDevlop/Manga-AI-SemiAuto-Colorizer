"""Base CRUD repositories for the colorization domain entities.

Defines repositories for ``MaskArtifact`` and ``ColorizationJob``. All
operations are async and backed by an injected SQLAlchemy async session. Only
metadata and storage paths are stored; no binary image content is kept in the
database.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.colorization.models import ColorizationJob, MaskArtifact


class MaskArtifactRepository:
    """Repository for ``MaskArtifact`` entities.

    A mask artifact references one character appearance. Listings can be
    filtered by appearance id.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, artifact_id: UUID) -> MaskArtifact | None:
        """Return the mask artifact with the given id, or ``None`` if missing."""
        stmt: Select = select(MaskArtifact).where(MaskArtifact.id == artifact_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, appearance_id: UUID | None = None) -> list[MaskArtifact]:
        """Return mask artifacts, optionally filtered by appearance id."""
        stmt: Select = select(MaskArtifact).order_by(MaskArtifact.created_at)
        if appearance_id is not None:
            stmt = stmt.where(MaskArtifact.appearance_id == appearance_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, **kwargs: Any) -> MaskArtifact:
        """Create and persist a new mask artifact from the given attributes."""
        artifact = MaskArtifact(**kwargs)
        self.session.add(artifact)
        await self.session.commit()
        await self.session.refresh(artifact)
        return artifact

    async def update(self, artifact_id: UUID, **kwargs: Any) -> MaskArtifact | None:
        """Update the attributes of the mask artifact with the given id."""
        artifact = await self.get(artifact_id)
        if artifact is None:
            return None
        for key, value in kwargs.items():
            setattr(artifact, key, value)
        await self.session.commit()
        await self.session.refresh(artifact)
        return artifact

    async def delete(self, artifact_id: UUID) -> bool:
        """Delete the mask artifact with the given id. Returns ``False`` if absent."""
        artifact = await self.get(artifact_id)
        if artifact is None:
            return False
        await self.session.delete(artifact)
        await self.session.commit()
        return True

    async def exists(self, artifact_id: UUID) -> bool:
        """Return ``True`` when a mask artifact with the given id exists."""
        stmt: Select = (
            select(MaskArtifact.id).where(MaskArtifact.id == artifact_id).limit(1)
        )
        result = await self.session.execute(stmt)
        return result.first() is not None


class ColorizationJobRepository:
    """Repository for ``ColorizationJob`` entities.

    A job references one analysis. Listings can be filtered by analysis id
    and/or job state.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, job_id: UUID) -> ColorizationJob | None:
        """Return the colorization job with the given id, or ``None`` if missing."""
        stmt: Select = select(ColorizationJob).where(ColorizationJob.id == job_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        analysis_id: UUID | None = None,
        estado: str | None = None,
    ) -> list[ColorizationJob]:
        """Return jobs, optionally filtered by analysis id and/or state."""
        stmt: Select = select(ColorizationJob).order_by(ColorizationJob.created_at)
        if analysis_id is not None:
            stmt = stmt.where(ColorizationJob.analysis_id == analysis_id)
        if estado is not None:
            stmt = stmt.where(ColorizationJob.estado == estado)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, **kwargs: Any) -> ColorizationJob:
        """Create and persist a new colorization job from the given attributes."""
        job = ColorizationJob(**kwargs)
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def update(self, job_id: UUID, **kwargs: Any) -> ColorizationJob | None:
        """Update the attributes of the job with the given id."""
        job = await self.get(job_id)
        if job is None:
            return None
        for key, value in kwargs.items():
            setattr(job, key, value)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def delete(self, job_id: UUID) -> bool:
        """Delete the job with the given id. Returns ``False`` if absent."""
        job = await self.get(job_id)
        if job is None:
            return False
        await self.session.delete(job)
        await self.session.commit()
        return True

    async def exists(self, job_id: UUID) -> bool:
        """Return ``True`` when a job with the given id exists."""
        stmt: Select = (
            select(ColorizationJob.id).where(ColorizationJob.id == job_id).limit(1)
        )
        result = await self.session.execute(stmt)
        return result.first() is not None

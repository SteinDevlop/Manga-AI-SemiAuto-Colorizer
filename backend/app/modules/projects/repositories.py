"""Base CRUD repository for the ``Project`` entity.

Provides ``get``, ``list``, ``create``, ``update``, ``delete`` and ``exists``
operations backed by an injected SQLAlchemy async session. Only metadata is
persisted; no binary image content is stored in the database.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.projects.models import Project


class ProjectRepository:
    """Repository for ``Project`` aggregates.

    A project owns many pages. Lookups are performed by UUID primary key and,
    for uniqueness enforcement, by project name.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, project_id: UUID) -> Project | None:
        """Return the project with the given id, or ``None`` if missing."""
        stmt: Select = select(Project).where(Project.id == project_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self) -> list[Project]:
        """Return all projects ordered by creation time."""
        stmt: Select = select(Project).order_by(Project.created_at)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, **kwargs: Any) -> Project:
        """Create and persist a new project from the given attributes."""
        project = Project(**kwargs)
        self.session.add(project)
        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def update(self, project_id: UUID, **kwargs: Any) -> Project | None:
        """Update the attributes of the project with the given id."""
        project = await self.get(project_id)
        if project is None:
            return None
        for key, value in kwargs.items():
            setattr(project, key, value)
        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def delete(self, project_id: UUID) -> bool:
        """Delete the project with the given id. Returns ``False`` if absent."""
        project = await self.get(project_id)
        if project is None:
            return False
        await self.session.delete(project)
        await self.session.commit()
        return True

    async def exists(self, project_id: UUID) -> bool:
        """Return ``True`` when a project with the given id exists."""
        stmt: Select = (
            select(Project.id).where(Project.id == project_id).limit(1)
        )
        result = await self.session.execute(stmt)
        return result.first() is not None

    async def exists_by_name(self, nombre: str) -> bool:
        """Return ``True`` when a project with the given name exists."""
        stmt: Select = select(Project.id).where(Project.nombre == nombre).limit(1)
        result = await self.session.execute(stmt)
        return result.first() is not None

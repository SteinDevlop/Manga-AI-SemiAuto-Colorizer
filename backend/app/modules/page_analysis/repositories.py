"""Base CRUD repositories for the page analysis domain entities.

Defines repositories for ``Page``, ``Panel`` and ``Analysis``. All operations
are async and backed by an injected SQLAlchemy async session. Only metadata and
filesystem paths are stored; no binary image content is kept in the database.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.modules.page_analysis.models import Analysis, Panel
from app.modules.projects.models import Page
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession


class PageRepository:
    """Repository for ``Page`` entities.

    A page belongs to one project and owns many panels and analyses.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, page_id: UUID) -> Page | None:
        """Return the page with the given id, or ``None`` if missing."""
        stmt: Select = select(Page).where(Page.id == page_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, project_id: UUID | None = None) -> list[Page]:
        """Return pages, optionally filtered by project id."""
        stmt: Select = select(Page).order_by(Page.created_at)
        if project_id is not None:
            stmt = stmt.where(Page.project_id == project_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, **kwargs: Any) -> Page:
        """Create and persist a new page from the given attributes."""
        page = Page(**kwargs)
        self.session.add(page)
        await self.session.commit()
        await self.session.refresh(page)
        return page

    async def update(self, page_id: UUID, **kwargs: Any) -> Page | None:
        """Update the attributes of the page with the given id."""
        page = await self.get(page_id)
        if page is None:
            return None
        for key, value in kwargs.items():
            setattr(page, key, value)
        await self.session.commit()
        await self.session.refresh(page)
        return page

    async def delete(self, page_id: UUID) -> bool:
        """Delete the page with the given id. Returns ``False`` if absent."""
        page = await self.get(page_id)
        if page is None:
            return False
        await self.session.delete(page)
        await self.session.commit()
        return True

    async def exists(self, page_id: UUID) -> bool:
        """Return ``True`` when a page with the given id exists."""
        stmt: Select = select(Page.id).where(Page.id == page_id).limit(1)
        result = await self.session.execute(stmt)
        return result.first() is not None


class PanelRepository:
    """Repository for ``Panel`` entities.

    A panel belongs to one page.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, panel_id: UUID) -> Panel | None:
        """Return the panel with the given id, or ``None`` if missing."""
        stmt: Select = select(Panel).where(Panel.id == panel_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, page_id: UUID | None = None) -> list[Panel]:
        """Return panels, optionally filtered by page id."""
        stmt: Select = select(Panel).order_by(Panel.numero_orden)
        if page_id is not None:
            stmt = stmt.where(Panel.page_id == page_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, **kwargs: Any) -> Panel:
        """Create and persist a new panel from the given attributes."""
        panel = Panel(**kwargs)
        self.session.add(panel)
        await self.session.commit()
        await self.session.refresh(panel)
        return panel

    async def update(self, panel_id: UUID, **kwargs: Any) -> Panel | None:
        """Update the attributes of the panel with the given id."""
        panel = await self.get(panel_id)
        if panel is None:
            return None
        for key, value in kwargs.items():
            setattr(panel, key, value)
        await self.session.commit()
        await self.session.refresh(panel)
        return panel

    async def delete(self, panel_id: UUID) -> bool:
        """Delete the panel with the given id. Returns ``False`` if absent."""
        panel = await self.get(panel_id)
        if panel is None:
            return False
        await self.session.delete(panel)
        await self.session.commit()
        return True

    async def exists(self, panel_id: UUID) -> bool:
        """Return ``True`` when a panel with the given id exists."""
        stmt: Select = select(Panel.id).where(Panel.id == panel_id).limit(1)
        result = await self.session.execute(stmt)
        return result.first() is not None


class AnalysisRepository:
    """Repository for ``Analysis`` entities.

    ``page_id`` is unique, so an analysis can also be located by page.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, analysis_id: UUID) -> Analysis | None:
        """Return the analysis with the given id, or ``None`` if missing."""
        stmt: Select = select(Analysis).where(Analysis.id == analysis_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_page_id(self, page_id: UUID) -> Analysis | None:
        """Return the analysis for the given page, or ``None`` if missing."""
        stmt: Select = select(Analysis).where(Analysis.page_id == page_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, **kwargs: Any) -> Analysis:
        """Create and persist a new analysis from the given attributes."""
        analysis = Analysis(**kwargs)
        self.session.add(analysis)
        await self.session.commit()
        await self.session.refresh(analysis)
        return analysis

    async def update(self, analysis_id: UUID, **kwargs: Any) -> Analysis | None:
        """Update the attributes of the analysis with the given id."""
        analysis = await self.get(analysis_id)
        if analysis is None:
            return None
        for key, value in kwargs.items():
            setattr(analysis, key, value)
        await self.session.commit()
        await self.session.refresh(analysis)
        return analysis

    async def delete(self, analysis_id: UUID) -> bool:
        """Delete the analysis with the given id. Returns ``False`` if absent."""
        analysis = await self.get(analysis_id)
        if analysis is None:
            return False
        await self.session.delete(analysis)
        await self.session.commit()
        return True

    async def exists(self, analysis_id: UUID) -> bool:
        """Return ``True`` when an analysis with the given id exists."""
        stmt: Select = (
            select(Analysis.id).where(Analysis.id == analysis_id).limit(1)
        )
        result = await self.session.execute(stmt)
        return result.first() is not None

    async def exists_by_page_id(self, page_id: UUID) -> bool:
        """Return ``True`` when an analysis exists for the given page."""
        stmt: Select = select(Analysis.id).where(Analysis.page_id == page_id).limit(1)
        result = await self.session.execute(stmt)
        return result.first() is not None

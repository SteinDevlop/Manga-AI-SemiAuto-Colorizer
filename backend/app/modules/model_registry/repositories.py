"""Repositorio concreto de ``ModelManifest`` con SQLAlchemy async.

Implementa el puerto ``ModelManifestRepository`` definido en los casos de uso
de aplicación, sobre la tabla existente ``model_manifests``. Incluye además
la consulta de trabajos en ejecución (S19) para proteger modelos en uso.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.modules.colorization.models import ColorizationJob
from app.modules.colorization.states import ACTIVE_STATES, TERMINAL_STATES
from app.modules.model_registry.models import ModelManifest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

#: Estados de job que se consideran "en ejecución" (no terminales).
_NON_TERMINAL_STATES = tuple(s for s in ACTIVE_STATES if s not in TERMINAL_STATES)


class ModelManifestRepository:
    """Repositorio de manifiestos de modelo.

    Todos los métodos son asíncronos y están respaldados por una sesión
    SQLAlchemy async inyectada.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # -- CRUD -----------------------------------------------------------

    async def list(self) -> list[ModelManifest]:
        """Retorna todos los manifiestos ordenados por creación."""
        stmt = select(ModelManifest).order_by(ModelManifest.created_at)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> ModelManifest:
        """Crea y persiste un manifiesto, retornando la instancia persistida."""
        manifest = ModelManifest(**kwargs)
        self.session.add(manifest)
        await self.session.commit()
        await self.session.refresh(manifest)
        return manifest

    async def get(self, *, manifest_id: UUID) -> ModelManifest | None:
        """Retorna el manifiesto con el id dado, o ``None`` si no existe."""
        stmt = select(ModelManifest).where(ModelManifest.id == manifest_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(
        self, *, manifest_id: UUID, **kwargs: Any
    ) -> ModelManifest | None:
        """Actualiza los atributos del manifiesto con el id dado."""
        manifest = await self.get(manifest_id=manifest_id)
        if manifest is None:
            return None
        for key, value in kwargs.items():
            setattr(manifest, key, value)
        await self.session.commit()
        await self.session.refresh(manifest)
        return manifest

    async def delete(self, manifest_id: UUID) -> bool:
        """Elimina el manifiesto con el id dado. Retorna ``False`` si no existía."""
        manifest = await self.get(manifest_id=manifest_id)
        if manifest is None:
            return False
        await self.session.delete(manifest)
        await self.session.commit()
        return True

    async def exists(self, manifest_id: UUID) -> bool:
        """Retorna ``True`` cuando existe un manifiesto con el id dado."""
        stmt = select(ModelManifest.id).where(ModelManifest.id == manifest_id).limit(1)
        result = await self.session.execute(stmt)
        return result.first() is not None

    # -- S19: protección de uso en curso --------------------------------

    async def tiene_trabajos_en_ejecucion(self, manifest_id: UUID) -> bool:
        """Retorna True si hay jobs de colorización no terminales vinculados.

        Como la tabla ``colorization_jobs`` no tiene FK a
        ``model_manifests``, se vincula por coincidencia del ``version_modelo``
        del job con la versión del manifiesto. Cualquier job en estado no
        terminal impide desactivar o eliminar el modelo.
        """
        manifest = await self.get(manifest_id=manifest_id)
        if manifest is None:
            return False
        stmt = select(ColorizationJob.id).where(
            ColorizationJob.version_modelo == manifest.version,
            ColorizationJob.estado.in_(_NON_TERMINAL_STATES),
        ).limit(1)
        result = await self.session.execute(stmt)
        return result.first() is not None

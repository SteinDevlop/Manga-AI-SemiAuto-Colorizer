"""Engine y sesión de base de datos asíncrona para el backend.

Expone ``engine``, ``async_session_factory`` y la dependencia ``get_session``
para inyección en rutas y casos de uso. La URL de conexión proviene de
``app.core.config.get_settings`` (DATABASE_URL).
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provee una sesión de base de datos async por request o caso de uso.

    Uso como dependencia de FastAPI:

    .. code:: python

        @app.get("/projects/{project_id}")
        async def get_project(project_id: UUID, session: AsyncSession = Depends(get_session)):
            ...
    """
    async with async_session_factory() as session:
        yield session

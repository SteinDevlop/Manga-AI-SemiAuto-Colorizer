"""Base declarativa de SQLAlchemy 2 para todas las entidades de dominio.

Proporciona columnas comunes (id UUID, created_at, updated_at) a todos los
modelos del dominio, siguiendo el contrato de identificadores UUID y fechas
UTC ISO-8601 acordado en P0.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Clase base para todos los modelos SQLAlchemy del dominio.

    Cada entidad hereda de esta clase y obtiene automáticamente:
    - ``id``: clave primaria UUID generada en Python.
    - ``created_at``: marca de tiempo UTC de creación.
    - ``updated_at``: marca de tiempo UTC de última actualización.
    """

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

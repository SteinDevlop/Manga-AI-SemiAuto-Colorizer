"""Entidad ORM del Model Registry.

Mapea ``ModelManifest`` a la tabla existente ``model_manifests`` (migración
``0001_initial_schema``). Como la tabla ya fue creada, este modelo solo
declara las columnas que existen y expone propiedades de conveniencia para
los campos de S12 que no tienen columna propia (se almacenan dentro de las
columnas JSON ``capacidades`` y ``parametros_soportados``).

Mapeo de columnas existentes a campos de S12:
- ``id``, ``nombre_modelo``, ``version``, ``created_at``, ``updated_at`` -> 1:1
- ``familia`` -> ``tarea`` (colorización, segmentación, análisis)
- ``fuente`` -> ``source_type`` (``local_file`` | ``api``)
- ``hash_pesos`` -> checksum SHA-256 del peso/archivo del modelo
- ``estado`` -> ``is_active`` (``disponible`` = activo, ``deshabilitado`` = inactivo)
- ``capacidades`` (JSON) -> ``descripcion``, ``parametros``, ``formato``,
  ``salud`` (ok | error | no_verificado), ``is_default``
- ``parametros_soportados`` (JSON) -> credenciales de API cifradas y
  parámetros por defecto (timeout, reintentos)
"""

from __future__ import annotations

from typing import Any

from app.infrastructure.database.base import Base
from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column


class ModelManifest(Base):
    """Modelo de manifiesto de modelo registrado.

    Persiste solo metadatos y rutas; el binario del modelo vive en el
    almacenamiento de artefactos (artifact_type ``models``) y las claves de
    API se almacenan cifradas (S17).
    """

    __tablename__ = "model_manifests"

    nombre_modelo: Mapped[str] = mapped_column(String, nullable=False)
    familia: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=False)
    hash_pesos: Mapped[str | None] = mapped_column(String, nullable=True)
    licencia: Mapped[str | None] = mapped_column(String, nullable=True)
    fuente: Mapped[str | None] = mapped_column(String, nullable=True)
    capacidades: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    requisitos_hardware: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )
    estado: Mapped[str] = mapped_column(
        String, nullable=False, server_default="disponible"
    )
    parametros_soportados: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )

    # ------------------------------------------------------------------
    # Propiedades de conveniencia para campos de S12 sin columna propia
    # ------------------------------------------------------------------

    @property
    def nombre(self) -> str:
        return self.nombre_modelo

    @property
    def tarea(self) -> str:
        return self.familia

    @property
    def source_type(self) -> str | None:
        return self.fuente

    @property
    def formato(self) -> str | None:
        return (self.capacidades or {}).get("formato")

    @property
    def is_active(self) -> bool:
        return self.estado == "disponible"

    @property
    def health_state(self) -> str:
        return (self.capacidades or {}).get("salud", "no_verificado")

    @property
    def descripcion(self) -> str | None:
        return (self.capacidades or {}).get("descripcion")

    @property
    def parametros(self) -> dict[str, Any]:
        return (self.capacidades or {}).get("parametros", {}) or {}

    @property
    def api_key_enc(self) -> str | None:
        return (self.parametros_soportados or {}).get("api_key_enc")

    @property
    def is_default(self) -> bool:
        return bool((self.capacidades or {}).get("is_default"))

    def to_dict(self) -> dict[str, Any]:
        """Serializa a diccionario sin exponer secretos cifrados."""
        return {
            "id": str(self.id),
            "nombre": self.nombre_modelo,
            "tarea": self.familia,
            "version": self.version,
            "source_type": self.fuente,
            "formato": self.formato,
            "is_active": self.is_active,
            "salud": self.health_state,
            "descripcion": self.descripcion,
            "parametros": self.parametros,
            "hash_pesos": self.hash_pesos,
            "licencia": self.licencia,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

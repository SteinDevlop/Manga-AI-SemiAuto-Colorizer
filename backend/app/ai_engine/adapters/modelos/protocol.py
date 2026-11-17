"""Interfaz común (Protocolo) de adaptadores de modelos del Model Registry.

Define el contrato que todo adaptador de modelo debe cumplir para que el
pipeline de inferencia consuma modelos únicamente a través de esta interfaz,
sin acoplamiento a un formato o proveedor concreto. Agregar un formato nuevo
es crear un adaptador y registrarlo, sin tocar el resto del sistema.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ModelAdapterProtocol(Protocol):
    """Protocolo común para adaptadores de modelos.

    Métodos:
    * ``validate`` — verifica que el recurso del modelo sea válido antes de
      cargarlo (extensión, tamaño, checksum, credenciales, conexión).
    * ``load`` — carga el modelo en memoria para inferencia.
    * ``unload`` — descarga el modelo y libera recursos.
    * ``infer`` — ejecuta inferencia sobre una entrada y retorna el resultado.
    * ``health_check`` — verifica que el modelo esté operativo sin ejecutar
      inferencia pesada (carga ligera o prueba de conexión).
    """

    @property
    def model_id(self) -> str:
        """Identificador estable del modelo adaptado."""

    @property
    def formato(self) -> str:
        """Formato del modelo (ej. ``pt``, ``onnx``, ``api``)."""

    async def validate(self, *, resource: Any) -> None:
        """Validar el recurso del modelo antes de cargarlo.

        Raises:
            ValueError: si el recurso no es válido.
        """
        ...

    async def load(self) -> None:
        """Cargar el modelo en memoria."""

    async def unload(self) -> None:
        """Descargar el modelo y liberar recursos."""

    async def infer(self, *, inputs: dict[str, Any]) -> dict[str, Any]:
        """Ejecutar inferencia sobre ``inputs`` y retornar el resultado."""

    async def health_check(self) -> dict[str, Any]:
        """Verificar que el modelo esté operativo.

        Returns:
            dict con al menos ``{"ok": bool, "detail": str}``.
        """
        ...

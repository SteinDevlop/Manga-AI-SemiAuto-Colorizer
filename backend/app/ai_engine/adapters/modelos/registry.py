"""Registro de adaptadores de modelos.

Mapea cada formato (``pt``, ``onnx``, ``api``) a su clase adaptadora.
Agregar un formato/proveedor nuevo es crear un adaptador y registrarlo aquí,
sin tocar el resto del sistema.
"""

from __future__ import annotations

from typing import Type

from .protocol import ModelAdapterProtocol

#: Mapeo de formato -> clase adaptadora.
ADAPTER_REGISTRY: dict[str, Type[ModelAdapterProtocol]] = {}


def register_adapter(formato: str, adapter_class: Type[ModelAdapterProtocol]) -> None:
    """Registrar una clase adaptadora para el ``formato`` dado.

    Args:
        formato: Identificador del formato (ej. ``pt``, ``onnx``, ``api``).
        adapter_class: Clase que implementa ``ModelAdapterProtocol``.
    """
    key = formato.lower().strip()
    ADAPTER_REGISTRY[key] = adapter_class


def resolve_adapter(formato: str) -> Type[ModelAdapterProtocol]:
    """Resolver la clase adaptadora para el ``formato`` dado.

    Raises:
        ValueError: si no hay un adaptador registrado para el formato.
    """
    key = formato.lower().strip()
    if key not in ADAPTER_REGISTRY:
        raise ValueError(
            f"No hay adaptador registrado para el formato '{formato}'. "
            f"Formatos disponibles: {sorted(ADAPTER_REGISTRY)}."
        )
    return ADAPTER_REGISTRY[key]


__all__ = ["ADAPTER_REGISTRY", "register_adapter", "resolve_adapter"]

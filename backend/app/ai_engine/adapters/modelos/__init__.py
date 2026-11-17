"""Adaptadores de modelos para el Model Registry.

Expone la interfaz común de adaptadores, el registro que mapea formato
-> clase adaptador y las implementaciones concretas para PyTorch (.pt),
ONNX (.onnx) y APIs externas.
"""

from __future__ import annotations

from .protocol import ModelAdapterProtocol
from .registry import ADAPTER_REGISTRY, register_adapter, resolve_adapter

__all__ = [
    "ModelAdapterProtocol",
    "ADAPTER_REGISTRY",
    "register_adapter",
    "resolve_adapter",
]

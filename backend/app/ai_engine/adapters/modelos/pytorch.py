"""Adaptador de modelos PyTorch (.pt).

Carga pesos con ``torch.load(..., weights_only=True)`` para evitar la
ejecución de código arbitrario vía pickle que permite el ``torch.load`` por
defecto. Preferir ONNX o safetensors cuando sea posible.

Nota de seguridad (S15): los archivos .pt pueden contener pickle arbitrario
que se ejecuta al cargarse. ``weights_only=True`` restringe la carga a
tensores y colecciones básicas, mitigando el riesgo. Documentado aquí y
en la docstring de ``load``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.ai_engine.adapters.modelos.protocol import ModelAdapterProtocol
from app.ai_engine.adapters.modelos.registry import register_adapter
from app.core.logging import get_logger

logger = get_logger(__name__)

#: Extensiones admitidas por este adaptador.
_PT_EXTENSIONS = frozenset({".pt", ".pth"})


class PyTorchModelAdapter(ModelAdapterProtocol):
    """Adaptador para modelos PyTorch serializados en disco (.pt / .pth)."""

    def __init__(self, *, model_id: str, ruta_archivo: str) -> None:
        self._model_id = model_id
        self._ruta_archivo = ruta_archivo
        self._model: Any = None
        self._loaded = False

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def formato(self) -> str:
        return "pt"

    async def validate(self, *, resource: Any) -> None:
        """Validar que el archivo .pt exista y tenga extensión válida."""
        path = Path(resource)
        if not path.is_file():
            raise ValueError(f"Archivo de modelo no encontrado: {path}")
        if path.suffix.lower() not in _PT_EXTENSIONS:
            raise ValueError(
                f"Extensión no admitida para PyTorch: {path.suffix}. "
                f"Use uno de {sorted(_PT_EXTENSIONS)}."
            )

    async def load(self) -> None:
        """Cargar el modelo PyTorch con ``weights_only=True``.

        Seguridad (S15): se usa ``weights_only=True`` para evitar la
        ejecución de código arbitrario vía pickle. Si el entorno no tiene
        torch instalado, la carga falla de forma controlada.
        """
        path = Path(self._ruta_archivo)
        try:
            import torch  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - optional heavy dep
            self._loaded = False
            self._model = None
            raise RuntimeError(
                "torch no está instalado; no se puede cargar un modelo .pt. "
                "Instale torch o use un modelo ONNX/API."
            ) from exc

        try:
            self._model = torch.load(str(path), map_location="cpu", weights_only=True)
            self._loaded = True
            logger.info("Modelo PyTorch cargado: %s", path)
        except Exception as exc:  # noqa: BLE001
            self._loaded = False
            self._model = None
            logger.error("Error cargando modelo PyTorch %s: %s", path, exc)
            raise

    async def unload(self) -> None:
        self._model = None
        self._loaded = False
        logger.info("Modelo PyTorch descargado: %s", self._model_id)

    async def infer(self, *, inputs: dict[str, Any]) -> dict[str, Any]:
        if not self._loaded or self._model is None:
            raise RuntimeError(f"Modelo {self._model_id} no está cargado.")
        # Placeholder: el adaptador concreto expone el objeto cargado para
        # que el pipeline real ejecute inferencia sobre él.
        return {
            "model_id": self._model_id,
            "formato": self.formato,
            "outputs": {},
            "note": "inferencia no implementada para este adaptador base",
        }

    async def health_check(self) -> dict[str, Any]:
        path = Path(self._ruta_archivo)
        if not path.is_file():
            return {"ok": False, "detail": f"Archivo no encontrado: {path}"}
        try:
            await self.load()
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "detail": str(exc)}
        finally:
            await self.unload()
        return {"ok": True, "detail": "modelo .pt cargable con weights_only=True"}


register_adapter("pt", PyTorchModelAdapter)
register_adapter("pth", PyTorchModelAdapter)


__all__ = ["PyTorchModelAdapter"]

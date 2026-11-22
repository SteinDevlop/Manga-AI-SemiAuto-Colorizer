"""Adaptador de modelos ONNX (.onnx).

Carga modelos ONNX mediante onnxruntime. ONNX es el formato preferido
sobre .pt por S15 (evita la ejecución de código arbitrario vía pickle).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.ai_engine.adapters.modelos.protocol import ModelAdapterProtocol
from app.ai_engine.adapters.modelos.registry import register_adapter
from app.core.logging import get_logger

logger = get_logger(__name__)

_ONNX_EXTENSIONS = frozenset({".onnx"})


class OnnxModelAdapter(ModelAdapterProtocol):
    """Adaptador para modelos ONNX en disco (.onnx)."""

    def __init__(self, *, model_id: str, ruta_archivo: str) -> None:
        self._model_id = model_id
        self._ruta_archivo = ruta_archivo
        self._session: Any = None
        self._loaded = False

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def formato(self) -> str:
        return "onnx"

    async def validate(self, *, resource: Any) -> None:
        path = Path(resource)
        if not path.is_file():
            raise ValueError(f"Archivo de modelo no encontrado: {path}")
        if path.suffix.lower() not in _ONNX_EXTENSIONS:
            raise ValueError(
                f"Extensión no admitida para ONNX: {path.suffix}. "
                f"Use uno de {sorted(_ONNX_EXTENSIONS)}."
            )

    async def load(self) -> None:
        path = Path(self._ruta_archivo)
        try:
            import onnxruntime as ort  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - optional heavy dep
            self._loaded = False
            self._session = None
            raise RuntimeError(
                "onnxruntime no está instalado; no se puede cargar un modelo .onnx."
            ) from exc

        try:
            self._session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
            self._loaded = True
            logger.info("Modelo ONNX cargado: %s", path)
        except Exception as exc:  # noqa: BLE001
            self._loaded = False
            self._session = None
            logger.error("Error cargando modelo ONNX %s: %s", path, exc)
            raise

    async def unload(self) -> None:
        self._session = None
        self._loaded = False
        logger.info("Modelo ONNX descargado: %s", self._model_id)

    async def infer(self, *, inputs: dict[str, Any]) -> dict[str, Any]:
        if not self._loaded or self._session is None:
            raise RuntimeError(f"Modelo {self._model_id} no está cargado.")
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
        return {"ok": True, "detail": "modelo .onnx cargable con onnxruntime"}


register_adapter("onnx", OnnxModelAdapter)


__all__ = ["OnnxModelAdapter"]

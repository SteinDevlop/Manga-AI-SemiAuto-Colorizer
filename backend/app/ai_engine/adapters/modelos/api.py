"""Adaptador de modelos para APIs externas.

Registra proveedor/nombre, URL base, método de autenticación, clave/token,
modelo/endpoint a invocar y parámetros por defecto (timeout, reintentos).
La prueba de conexión (``health_check``) se llama ANTES de guardar (S16);
si falla, no se guarda y se devuelve error claro.
"""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.ai_engine.adapters.modelos.protocol import ModelAdapterProtocol
from app.ai_engine.adapters.modelos.registry import register_adapter

logger = get_logger(__name__)


class ApiModelAdapter(ModelAdapterProtocol):
    """Adaptador para modelos expuestos mediante una API externa."""

    def __init__(
        self,
        *,
        model_id: str,
        base_url: str,
        auth_method: str = "bearer",
        api_key: str | None = None,
        endpoint: str = "/infer",
        modelo: str | None = None,
        timeout: float = 30.0,
        retries: int = 2,
    ) -> None:
        self._model_id = model_id
        self._base_url = base_url.rstrip("/")
        self._auth_method = auth_method
        self._api_key = api_key
        self._endpoint = endpoint
        self._modelo = modelo
        self._timeout = timeout
        self._retries = retries

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def formato(self) -> str:
        return "api"

    async def validate(self, *, resource: Any) -> None:
        """Validar credenciales y configuración de la API externa."""
        if not self._base_url:
            raise ValueError("base_url es obligatorio para modelos API.")
        if self._auth_method in ("bearer", "apikey") and not self._api_key:
            raise ValueError(
                f"api_key es obligatorio con auth_method='{self._auth_method}'."
            )

    async def load(self) -> None:
        """Las APIs externas no requieren carga en memoria."""
        logger.info("Adaptador API listo (sin carga local): %s", self._model_id)

    async def unload(self) -> None:
        """Sin recursos locales que liberar."""

    async def infer(self, *, inputs: dict[str, Any]) -> dict[str, Any]:
        import requests  # type: ignore[import-not-found]

        url = f"{self._base_url}{self._endpoint}"
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._auth_method == "bearer" and self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        elif self._auth_method == "apikey" and self._api_key:
            headers["X-API-Key"] = self._api_key

        payload = dict(inputs)
        if self._modelo:
            payload.setdefault("modelo", self._modelo)

        last_error: str | None = None
        for attempt in range(self._retries + 1):
            try:
                response = requests.post(
                    url, json=payload, headers=headers, timeout=self._timeout
                )
                response.raise_for_status()
                return {
                    "model_id": self._model_id,
                    "formato": self.formato,
                    "outputs": response.json()
                    if response.headers.get("content-type", "").startswith(
                        "application/json"
                    )
                    else {"texto": response.text},
                }
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)
        raise RuntimeError(f"Error invocando API externa {self._model_id}: {last_error}")

    async def health_check(self) -> dict[str, Any]:
        """Probar conexión a la API sin ejecutar inferencia pesada."""
        import requests  # type: ignore[import-not-found]

        try:
            await self.validate(resource=self._base_url)
        except ValueError as exc:
            return {"ok": False, "detail": str(exc)}

        url = f"{self._base_url}{self._endpoint}"
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._auth_method == "bearer" and self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        elif self._auth_method == "apikey" and self._api_key:
            headers["X-API-Key"] = self._api_key

        try:
            response = requests.post(
                url, json={"health_check": True, "modelo": self._modelo},
                headers=headers, timeout=self._timeout,
            )
            if response.status_code < 500:
                return {
                    "ok": True,
                    "detail": f"API respondió (HTTP {response.status_code}).",
                }
            return {
                "ok": False,
                "detail": f"API respondió con error HTTP {response.status_code}.",
            }
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "detail": f"No se pudo conectar a la API: {exc}"}


register_adapter("api", ApiModelAdapter)


__all__ = ["ApiModelAdapter"]

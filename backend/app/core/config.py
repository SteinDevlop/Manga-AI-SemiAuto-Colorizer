import logging
from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings

_log = logging.getLogger(__name__)

# Valores por defecto que NUNCA deben llegar a producción.
# Valor por defecto SOLO para desarrollo local (>=32 bytes para no disparar avisos de PyJWT).
DEV_SECRET_KEY = "dev-only-insecure-secret-key-do-not-use-in-production"
_INSECURE_SECRET_KEYS = frozenset(
    {"", "dev-secret-change-in-production", DEV_SECRET_KEY, "changeme", "secret", "change-me"}
)
_MIN_SECRET_KEY_LENGTH = 32  # HS256 requiere una clave de al menos 256 bits


class Settings(BaseSettings):
    """Configuración tipada del backend mediante variables de entorno."""

    PROJECT_NAME: str = "Manga Colorizer API"
    PROJECT_VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # Base de datos
    DATABASE_URL: str = "postgresql+asyncpg://manga:manga@localhost:5432/manga"

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Entorno de ejecución: "development" | "test" | "production".
    # En producción la configuración insegura aborta el arranque (fail-fast).
    ENVIRONMENT: str = "development"

    # Seguridad (autenticación JWT con flujo OAuth2 de contraseña)
    SECRET_KEY: str = DEV_SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # Usuario inicial opcional: si ambas variables están definidas y la tabla
    # de usuarios está vacía, se crea al arrancar la API. Sin ellas, usar
    # ``python -m app.cli create-user``.
    FIRST_ADMIN_EMAIL: str = ""
    FIRST_ADMIN_PASSWORD: str = ""

    # CORS: orígenes permitidos del frontend, separados por coma.
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Almacenamiento local
    STORAGE_ROOT: str = "./data"

    # Subida de archivos
    MAX_UPLOAD_BYTES: int = 50 * 1024 * 1024  # 50 MB por defecto para páginas
    MAX_MODEL_UPLOAD_BYTES: int = 500 * 1024 * 1024  # 500 MB para archivos de modelo (.pt/.onnx)

    # Cifrado de secretos (S17): clave base para Fernet. En producción debe
    # definirse mediante variable de entorno ENCRYPTION_KEY.
    ENCRYPTION_KEY: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.strip().lower() in {"production", "prod"}

    @model_validator(mode="after")
    def _validate_security(self) -> "Settings":
        """Aborta el arranque en producción con secretos débiles o ausentes.

        En desarrollo/pruebas solo emite advertencias para no frenar el flujo
        local; en producción la API no debe iniciar con claves de ejemplo.
        """
        problems: list[str] = []
        if (
            self.SECRET_KEY in _INSECURE_SECRET_KEYS
            or len(self.SECRET_KEY) < _MIN_SECRET_KEY_LENGTH
        ):
            problems.append(
                f"SECRET_KEY debe definirse con al menos {_MIN_SECRET_KEY_LENGTH} caracteres "
                'aleatorios (ej.: python -c "import secrets; print(secrets.token_urlsafe(48))")'
            )
        if not self.ENCRYPTION_KEY:
            problems.append(
                'ENCRYPTION_KEY debe definirse (Fernet; ej.: python -c "from '
                'cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"). '
                "Sin ella las claves de API de modelos se cifran con una clave derivada pública."
            )
        if self.ALGORITHM not in {"HS256", "HS384", "HS512"}:
            problems.append("ALGORITHM debe ser HS256, HS384 o HS512")
        if problems:
            if self.is_production:
                raise ValueError(
                    "Configuración insegura para ENVIRONMENT=production."
                )
            # En desarrollo, advertimos sin exponer detalles sensibles del problema.
            _log.warning(
                "Configuración insegura detectada en entorno no producción; revisar configuración antes de despliegue."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Devuelve la instancia singleton de settings."""
    return Settings()


def get_fernet():
    """Retorna una instancia Fernet usando ``ENCRYPTION_KEY``.

    La clave debe ser una URL-safe base64-encoded de 32 bytes. Si no está
    configurada, se genera una clave derivativa determinista para desarrollo;
    nunca se usa para producción sin configurar la variable de entorno.
    """
    import base64

    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    settings = get_settings()
    raw = settings.ENCRYPTION_KEY
    if not raw:
        # Clave derivativa solo para desarrollo; se advierte en el log.
        import logging

        logging.getLogger(__name__).warning(
            "ENCRYPTION_KEY no configurada; usando clave derivativa de desarrollo."
        )
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"manga-dev-salt",
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(b"dev-encryption-key"))
    else:
        key = raw.encode() if isinstance(raw, str) else raw
    return Fernet(key)


__all__ = [
    "Settings",
    "get_settings",
    "get_fernet",
]

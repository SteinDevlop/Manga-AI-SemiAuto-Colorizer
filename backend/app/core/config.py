from functools import lru_cache

from pydantic_settings import BaseSettings


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

    # Seguridad
    SECRET_KEY: str = "dev-secret-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Almacenamiento local
    STORAGE_ROOT: str = "./data"

    # Subida de archivos
    MAX_UPLOAD_BYTES: int = 50 * 1024 * 1024  # 50 MB por defecto

    # Cifrado de secretos (S17): clave base para Fernet. En producción debe
    # definirse mediante variable de entorno ENCRYPTION_KEY.
    ENCRYPTION_KEY: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


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
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import base64

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

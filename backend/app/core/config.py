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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """Devuelve la instancia singleton de settings."""
    return Settings()

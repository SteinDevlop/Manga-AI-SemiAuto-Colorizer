"""Placeholder de utilidades de seguridad (hashing, tokens, etc.)."""

from typing import Any


def create_access_token(subject: str | Any, expires_delta: int | None = None) -> str:
    """Genera un token de acceso (placeholder)."""
    raise NotImplementedError("create_access_token no está implementado todavía")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash (placeholder)."""
    raise NotImplementedError("verify_password no está implementado todavía")


def get_password_hash(password: str) -> str:
    """Genera el hash de una contraseña (placeholder)."""
    raise NotImplementedError("get_password_hash no está implementado todavía")

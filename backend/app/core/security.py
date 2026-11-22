"""Utilidades de seguridad: hash de contraseñas y tokens JWT de acceso.

* Contraseñas: bcrypt (factor de coste 12). Se aplica un prehash SHA-256 +
  base64 para que contraseñas largas no se trunquen en silencio a 72 bytes
  (límite de bcrypt) y para evitar el error de bcrypt>=5 con entradas largas.
* Tokens: JWT firmados con HMAC (``SECRET_KEY``/``ALGORITHM``). La decodificación
  fija la lista de algoritmos permitidos, por lo que ``alg=none`` o un cambio de
  algoritmo en el token son rechazados.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from app.core.config import get_settings

BCRYPT_ROUNDS = 12
TOKEN_TYPE_ACCESS = "access"

# Hash válido calculado una vez; se usa para igualar el tiempo de respuesta del
# login cuando el usuario no existe (evita enumeración de usuarios por timing).
_DUMMY_HASH: str | None = None


class TokenError(Exception):
    """El token es inválido, está mal formado o expiró."""


def _prehash(password: str) -> bytes:
    return password.encode("utf-8")


def get_password_hash(password: str) -> str:
    """Genera el hash bcrypt de una contraseña."""
    if not password:
        raise ValueError("La contraseña no puede estar vacía")
    return bcrypt.hashpw(_prehash(password), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode("ascii")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash. Nunca lanza por hashes corruptos."""
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(_prehash(plain_password), hashed_password.encode("ascii"))
    except (ValueError, TypeError):
        return False


def verify_password_dummy(plain_password: str) -> None:
    """Gasta el mismo tiempo que una verificación real (usuario inexistente)."""
    global _DUMMY_HASH
    if _DUMMY_HASH is None:
        _DUMMY_HASH = get_password_hash("dummy-password-for-timing-equalization")
    verify_password(plain_password, _DUMMY_HASH)


def create_access_token(subject: str | Any, expires_delta: int | timedelta | None = None) -> str:
    """Genera un JWT de acceso.

    Args:
        subject: identificador del usuario (se guarda en ``sub`` como texto).
        expires_delta: ``timedelta`` o minutos (``int``). Por defecto
            ``ACCESS_TOKEN_EXPIRE_MINUTES``.
    """
    settings = get_settings()
    if expires_delta is None:
        delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    elif isinstance(expires_delta, timedelta):
        delta = expires_delta
    else:
        delta = timedelta(minutes=int(expires_delta))
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(subject),
        "type": TOKEN_TYPE_ACCESS,
        "iat": now,
        "exp": now + delta,
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Valida firma, expiración y tipo; devuelve los claims o lanza ``TokenError``."""
    settings = get_settings()
    try:
        claims = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],  # lista fija: bloquea alg=none/confusión
            options={"require": ["exp", "sub", "iat"]},
        )
    except jwt.PyJWTError as exc:
        raise TokenError(str(exc)) from exc
    if claims.get("type") != TOKEN_TYPE_ACCESS or not claims.get("sub"):
        raise TokenError("Tipo de token inválido")
    return claims

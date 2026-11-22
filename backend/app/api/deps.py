"""Dependencias compartidas de la API: autenticación del usuario actual."""

from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import TokenError, decode_access_token
from app.infrastructure.database.session import get_session
from app.modules.users.models import User
from app.modules.users.repositories import UserRepository

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{get_settings().API_V1_STR}/auth/token",
    auto_error=False,  # el 401 se emite abajo con el envelope y cabecera estándar
)

_BEARER = {"WWW-Authenticate": "Bearer"}


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "unauthorized", "message": message},
        headers=_BEARER,
    )


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Resuelve el usuario a partir del Bearer token o responde 401.

    Mensajes deliberadamente genéricos: no distinguen firma inválida de usuario
    inexistente para no filtrar información a un atacante.
    """
    if not token:
        raise _unauthorized("Autenticación requerida")
    try:
        claims = decode_access_token(token)
        user_id = UUID(claims["sub"])
    except (TokenError, ValueError):
        raise _unauthorized("Credenciales inválidas o sesión expirada") from None

    user = await UserRepository(session).get(user_id)
    if user is None or not user.is_active:
        raise _unauthorized("Credenciales inválidas o sesión expirada")
    return user


async def get_current_admin(user: User = Depends(get_current_user)) -> User:
    """Exige rol administrador (p. ej. registrar o eliminar modelos)."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "forbidden", "message": "Se requieren permisos de administrador"},
        )
    return user

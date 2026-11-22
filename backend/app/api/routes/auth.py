"""Autenticación: flujo OAuth2 de contraseña con JWT (``/api/v1/auth``).

No existe registro público: cualquiera podría crearse una cuenta y anular el
sentido de la autenticación. Los usuarios se crean con ``python -m app.cli
create-user`` o con ``FIRST_ADMIN_EMAIL``/``FIRST_ADMIN_PASSWORD`` al arrancar.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque

from app.api.deps import get_session_dep, login_form_dep
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
    verify_password_dummy,
)
from app.modules.users.models import User
from app.modules.users.repositories import UserRepository, normalize_email
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 128


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: str
    email: str
    is_admin: bool


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=MAX_PASSWORD_LENGTH)
    new_password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)


# --- Limitador de intentos fallidos (en memoria, por proceso) ------------------
# Frena fuerza bruta básica. Con varios workers/réplicas cada proceso cuenta por
# separado: para producción a escala, mover a Redis o a un proxy (documentado).
_MAX_FAILURES = 5
_WINDOW_SECONDS = 15 * 60
_failures: dict[str, deque[float]] = defaultdict(deque)


def _throttle_key(request: Request, email: str) -> str:
    host = request.client.host if request.client else "unknown"
    return f"{host}|{normalize_email(email)}"


def _check_throttle(key: str) -> None:
    now = time.monotonic()
    attempts = _failures[key]
    while attempts and now - attempts[0] > _WINDOW_SECONDS:
        attempts.popleft()
    if len(attempts) >= _MAX_FAILURES:
        retry_after = max(1, int(_WINDOW_SECONDS - (now - attempts[0])))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "too_many_attempts",
                "message": "Demasiados intentos fallidos. Inténtalo más tarde.",
            },
            headers={"Retry-After": str(retry_after)},
        )


def reset_throttle() -> None:
    """Limpia contadores (usado por las pruebas)."""
    _failures.clear()


@router.post("/token", response_model=TokenResponse)
async def login(
    request: Request,
    form: OAuth2PasswordRequestForm = login_form_dep,
    session: AsyncSession = get_session_dep,
) -> TokenResponse:
    """Intercambia usuario/contraseña por un token de acceso (OAuth2 password flow)."""
    key = _throttle_key(request, form.username)
    _check_throttle(key)

    user = await UserRepository(session).get_by_email(form.username)
    if user is None:
        verify_password_dummy(form.password)  # iguala el tiempo de respuesta
        valid = False
    else:
        valid = verify_password(form.password, user.hashed_password) and user.is_active

    if not valid or user is None:
        _failures[key].append(time.monotonic())
        logger.warning("Login fallido para %s", normalize_email(form.username))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_credentials", "message": "Email o contraseña incorrectos"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    _failures.pop(key, None)
    settings = get_settings()
    logger.info("Login correcto: %s", user.id)
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserResponse)
async def me(user: User = get_current_user_dep) -> UserResponse:
    """Devuelve el usuario autenticado (el frontend lo usa para validar la sesión)."""
    return UserResponse(id=str(user.id), email=user.email, is_admin=user.is_admin)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    body: ChangePasswordRequest,
    user: User = get_current_user_dep,
    session: AsyncSession = get_session_dep,
) -> None:
    if not verify_password(body.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_credentials",
                "message": "La contraseña actual no es correcta",
            },
        )
    await UserRepository(session).update_password(user, get_password_hash(body.new_password))

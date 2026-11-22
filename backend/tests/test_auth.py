"""Pruebas de autenticación: JWT, hash de contraseñas y protección de rutas.

Usan la app real con SQLite en memoria (aiosqlite) sustituyendo ``get_session``.
"""

from __future__ import annotations

import re
import uuid
from datetime import timedelta

import jwt
import pytest
from app.api.routes import auth as auth_routes
from app.core import security
from app.core.config import get_settings
from app.infrastructure.database.base import Base
from app.infrastructure.database.session import get_session
from app.main import app
from app.modules.users.repositories import UserRepository
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

PASSWORD = "correct-horse-battery"
PUBLIC_ROUTES = {("GET", "/health"), ("POST", "/api/v1/auth/token")}


def _import_all_models() -> None:
    import app.modules.assets.models  # noqa: F401
    import app.modules.character_analysis.models  # noqa: F401
    import app.modules.character_configuration.models  # noqa: F401
    import app.modules.character_memory.models  # noqa: F401
    import app.modules.colorization.models  # noqa: F401
    import app.modules.model_registry.models  # noqa: F401
    import app.modules.page_analysis.models  # noqa: F401
    import app.modules.projects.models  # noqa: F401
    import app.modules.users.models  # noqa: F401


@pytest.fixture(autouse=True)
def _fast_bcrypt(monkeypatch):
    monkeypatch.setattr(security, "BCRYPT_ROUNDS", 4)  # acelera las pruebas
    auth_routes.reset_throttle()
    yield
    auth_routes.reset_throttle()


@pytest.fixture
def db():
    """TestClient sobre la app real con una BD SQLite en memoria ya migrada."""
    _import_all_models()
    engine = create_async_engine(
        "sqlite+aiosqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _override():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_session] = _override
    with TestClient(app) as client:

        async def _create_tables():
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

        client.portal.call(_create_tables)
        client._factory = factory  # type: ignore[attr-defined]
        yield client
    app.dependency_overrides.clear()


def make_user(
    client: TestClient, email="user@example.com", password=PASSWORD, admin=False, active=True
):
    async def _create():
        async with client._factory() as session:  # type: ignore[attr-defined]
            user = await UserRepository(session).create(
                email=email, hashed_password=security.get_password_hash(password), is_admin=admin
            )
            if not active:
                user.is_active = False
                await session.commit()
            return str(user.id)

    return client.portal.call(_create)


def login(client: TestClient, email="user@example.com", password=PASSWORD):
    return client.post("/api/v1/auth/token", data={"username": email, "password": password})


def auth_header(client: TestClient, **kw):
    token = login(client, **kw).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ------------------------------------------------------------------ unitarias
def test_password_hash_roundtrip_and_salting():
    h1, h2 = security.get_password_hash(PASSWORD), security.get_password_hash(PASSWORD)
    assert h1 != h2 and PASSWORD not in h1
    assert security.verify_password(PASSWORD, h1)
    assert not security.verify_password("otra-contraseña-distinta", h1)


def test_long_passwords_are_not_silently_truncated():
    base = "a" * 80  # bcrypt crudo ignoraría todo después del byte 72
    h = security.get_password_hash(base + "X")
    assert security.verify_password(base + "X", h)
    assert not security.verify_password(base + "Y", h)


def test_verify_password_never_raises_on_garbage():
    assert security.verify_password(PASSWORD, "no-es-un-hash") is False
    assert security.verify_password("", security.get_password_hash(PASSWORD)) is False


def test_token_roundtrip_and_minutes_int():
    token = security.create_access_token("abc", expires_delta=5)
    claims = security.decode_access_token(token)
    assert claims["sub"] == "abc" and claims["type"] == "access"
    assert 0 < claims["exp"] - claims["iat"] <= 300


def test_expired_token_rejected():
    token = security.create_access_token("abc", expires_delta=timedelta(seconds=-1))
    with pytest.raises(security.TokenError):
        security.decode_access_token(token)


def test_tampered_token_rejected():
    token = security.create_access_token("abc")
    head, payload, sig = token.split(".")
    with pytest.raises(security.TokenError):
        security.decode_access_token(f"{head}.{payload}.{sig[:-2]}AA")


def test_alg_none_token_rejected():
    forged = jwt.encode(
        {"sub": "abc", "type": "access", "iat": 1, "exp": 9999999999}, key="", algorithm="none"
    )
    with pytest.raises(security.TokenError):
        security.decode_access_token(forged)


def test_token_signed_with_other_key_or_wrong_type_rejected():
    s = get_settings()
    claims = {"sub": "x", "type": "access", "iat": 1, "exp": 9999999999}
    other_key = jwt.encode(claims, "otra-clave-distinta-de-32-bytes!!", algorithm=s.ALGORITHM)
    wrong_type = jwt.encode({**claims, "type": "refresh"}, s.SECRET_KEY, algorithm=s.ALGORITHM)
    for bad in (other_key, wrong_type):
        with pytest.raises(security.TokenError):
            security.decode_access_token(bad)


# ------------------------------------------------------- seguridad por defecto
def _sample_path(path: str) -> str:
    return re.sub(r"\{[^}]+\}", "00000000-0000-0000-0000-000000000000", path)


def _protected_routes():
    """Todas las operaciones del contrato OpenAPI salvo las públicas.

    Se usa el esquema OpenAPI (no ``app.routes``) porque las versiones recientes
    de FastAPI envuelven los routers incluidos y no los aplanan.
    """
    http = {"get", "post", "put", "patch", "delete"}
    return sorted(
        (method.upper(), path)
        for path, ops in app.openapi()["paths"].items()
        for method in ops
        if method in http
        and (method.upper(), path) not in PUBLIC_ROUTES
        and not path.startswith("/api/v1/auth/")
    )


def test_there_are_protected_routes_to_check():
    assert len(_protected_routes()) >= 20  # evita que la comprobación pase en vacío


@pytest.mark.parametrize("method,path", _protected_routes())
def test_every_business_route_requires_authentication(db, method, path):
    r = db.request(method, _sample_path(path))
    assert r.status_code == 401, f"{method} {path} quedó abierta (status {r.status_code})"
    assert r.headers["www-authenticate"] == "Bearer"
    assert r.json()["code"] == "unauthorized"


def test_auth_me_and_change_password_require_authentication(db):
    assert db.get("/api/v1/auth/me").status_code == 401
    assert db.post("/api/v1/auth/change-password", json={}).status_code == 401


def test_invalid_bearer_is_rejected_on_protected_route(db):
    r = db.get("/api/v1/projects", headers={"Authorization": "Bearer basura"})
    assert r.status_code == 401


def test_health_stays_public(db):
    assert db.get("/health").status_code == 200


# --------------------------------------------------------------- login y /me
def test_login_success_and_me(db):
    make_user(db)
    r = login(db)
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == get_settings().ACCESS_TOKEN_EXPIRE_MINUTES * 60
    me = db.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200 and me.json()["email"] == "user@example.com"
    assert "hashed_password" not in me.text


def test_authenticated_request_reaches_the_route(db):
    make_user(db)
    r = db.get("/api/v1/projects", headers=auth_header(db))
    assert r.status_code == 200


def test_login_is_case_insensitive_on_email(db):
    make_user(db, email="Mixed@Example.com")
    assert login(db, email="MIXED@example.COM").status_code == 200


def test_login_wrong_password_and_unknown_user_look_identical(db):
    make_user(db)
    wrong = login(db, password="incorrecta-incorrecta")
    unknown = login(db, email="nadie@example.com")
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["message"] == unknown.json()["message"]


def test_inactive_user_cannot_login_nor_reuse_token(db):
    uid = make_user(db, email="off@example.com")
    header = auth_header(db, email="off@example.com")

    async def _deactivate():
        async with db._factory() as s:  # type: ignore[attr-defined]
            u = await UserRepository(s).get(uuid.UUID(uid))
            u.is_active = False
            await s.commit()

    db.portal.call(_deactivate)
    assert db.get("/api/v1/auth/me", headers=header).status_code == 401
    assert login(db, email="off@example.com").status_code == 401


def test_login_throttle_after_repeated_failures(db):
    make_user(db)
    for _ in range(5):
        assert login(db, password="mala-mala-mala").status_code == 401
    blocked = login(db)  # incluso la contraseña correcta queda bloqueada
    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) > 0


def test_successful_login_resets_counter(db):
    make_user(db)
    for _ in range(4):
        login(db, password="mala-mala-mala")
    assert login(db).status_code == 200
    for _ in range(4):
        assert login(db, password="mala-mala-mala").status_code == 401


# ----------------------------------------------------------- roles y password
def test_model_registry_mutations_require_admin(db):
    make_user(db, email="user@example.com")
    make_user(db, email="admin@example.com", admin=True)
    user_h = auth_header(db, email="user@example.com")
    admin_h = auth_header(db, email="admin@example.com")
    assert db.get("/api/v1/models", headers=user_h).status_code == 200  # lectura: cualquier usuario
    assert db.post("/api/v1/models", headers=user_h).status_code == 403
    assert db.delete(f"/api/v1/models/{uuid.uuid4()}", headers=user_h).status_code == 403
    # Admin supera la autorización (falla después por cuerpo inválido, no por 403).
    assert db.post("/api/v1/models", headers=admin_h).status_code != 403


def test_change_password_flow(db):
    make_user(db)
    h = auth_header(db)
    bad_current = {"current_password": "equivocada", "new_password": "nueva-contraseña-123"}
    too_short = {"current_password": PASSWORD, "new_password": "corta"}
    ok = {"current_password": PASSWORD, "new_password": "nueva-contraseña-123"}
    assert db.post("/api/v1/auth/change-password", headers=h, json=bad_current).status_code == 400
    assert db.post("/api/v1/auth/change-password", headers=h, json=too_short).status_code == 422
    assert db.post("/api/v1/auth/change-password", headers=h, json=ok).status_code == 204
    assert login(db).status_code == 401
    assert login(db, password="nueva-contraseña-123").status_code == 200


def test_there_is_no_public_registration(db):
    for path in ("/api/v1/auth/register", "/api/v1/auth/signup", "/api/v1/users"):
        r = db.post(path, json={"email": "a@b.co", "password": PASSWORD})
        assert r.status_code in (401, 404, 405), path

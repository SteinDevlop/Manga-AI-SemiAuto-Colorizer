"""CLI administrativa del backend.

Uso::

    python -m app.cli create-user --email admin@example.com --admin
    # la contraseña se pide por prompt (no queda en el historial del shell)
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import sys

from app.api.routes.auth import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH
from app.core.security import get_password_hash
from app.infrastructure.database.session import async_session_factory
from app.modules.users.repositories import UserRepository


async def create_user(email: str, password: str, is_admin: bool) -> str:
    if not (MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH):
        raise SystemExit(
            f"La contraseña debe tener entre {MIN_PASSWORD_LENGTH} y {MAX_PASSWORD_LENGTH} caracteres."
        )
    if "@" not in email:
        raise SystemExit("Email inválido.")
    async with async_session_factory() as session:
        repo = UserRepository(session)
        if await repo.get_by_email(email) is not None:
            raise SystemExit(f"Ya existe un usuario con el email {email}.")
        user = await repo.create(
            email=email, hashed_password=get_password_hash(password), is_admin=is_admin
        )
        return str(user.id)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    cu = sub.add_parser("create-user", help="Crea un usuario")
    cu.add_argument("--email", required=True)
    cu.add_argument("--admin", action="store_true", help="Otorga rol administrador")
    cu.add_argument("--password-env", help="Lee la contraseña de esta variable de entorno")
    args = parser.parse_args(argv)

    if args.command == "create-user":
        import os

        password = os.environ.get(args.password_env, "") if args.password_env else ""
        if not password:
            password = getpass.getpass("Contraseña: ")
            if password != getpass.getpass("Repite la contraseña: "):
                print("Las contraseñas no coinciden.", file=sys.stderr)
                return 1
        user_id = asyncio.run(create_user(args.email, password, args.admin))
        print(f"Usuario creado: {user_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

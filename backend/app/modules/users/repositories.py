"""Repositorio de usuarios."""

from __future__ import annotations

from uuid import UUID

from app.modules.users.models import User
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


def normalize_email(email: str) -> str:
    return email.strip().lower()


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: UUID) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == normalize_email(email))
        )
        return result.scalar_one_or_none()

    async def count(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(User))
        return int(result.scalar_one())

    async def create(self, *, email: str, hashed_password: str, is_admin: bool = False) -> User:
        user = User(
            email=normalize_email(email), hashed_password=hashed_password, is_admin=is_admin
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_password(self, user: User, hashed_password: str) -> User:
        user.hashed_password = hashed_password
        await self.session.commit()
        await self.session.refresh(user)
        return user

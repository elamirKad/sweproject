from typing import Optional, TypeVar, Union
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

import models
from repositories.base import DatabaseRepository

Model = TypeVar("Model", bound=models.Base)


class UserRepository(DatabaseRepository[models.User]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.User, session)

    async def find_by_email(self, email: str) -> Optional[models.User]:
        """Find a user by email."""
        async with self.session.begin():
            stmt = select(self.model).where(self.model.email == email)
            result = await self.session.execute(stmt)
            user = result.scalars().first()
            return user

    async def find_by_phone(self, phone: str) -> Optional[models.User]:
        """Find a user by phone."""
        async with self.session.begin():
            stmt = select(self.model).where(self.model.phone == phone)
            result = await self.session.execute(stmt)
            user = result.scalars().first()
            return user

    async def update_password(self, user_id: Union[UUID, str], new_password: bytes) -> bool:
        """Update a user's password."""
        async with self.session.begin():
            stmt = update(self.model).where(self.model.id == user_id).values(password=new_password)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0


class RefreshTokenRepository(DatabaseRepository[models.RefreshToken]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.RefreshToken, session)

    async def get_refresh_token_by_token(self, token: str) -> Optional[models.RefreshToken]:
        stmt = select(self.model).where(self.model.token == token)
        result = await self.session.execute(stmt)
        return result.scalars().first()

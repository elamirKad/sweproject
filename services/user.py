from contextlib import asynccontextmanager
from typing import Optional
from uuid import UUID

from models import User
from database import get_session as AsyncSessionManager
from domains.user.exceptions import (
    InvalidCredentials,
    RefreshTokenExpired,
    RefreshTokenNotActive,
    RefreshTokenNotFound,
    TokenExpired,
    UserEmailAlreadyExists,
)
from domains.user.repository import RefreshTokenRepository, UserRepository
from domains.user.schemas import TokenPair, UserLoginForm, UserSignupForm, UserToDB
from utils.password import hash_password, verify_password
from utils.tokens import generate_token_pair, get_user_id_from_token


@asynccontextmanager
async def get_user_service():
    async with AsyncSessionManager() as session:
        try:
            user_repo = UserRepository(session)
            refresh_token_repo = RefreshTokenRepository(session)
            yield UserService(user_repo, refresh_token_repo)
        finally:
            await session.close()


class UserService:
    def __init__(self, user_repo: UserRepository, refresh_token_repo: RefreshTokenRepository):
        self.user_repo = user_repo
        self.refresh_token_repo = refresh_token_repo

    async def get_token_pair_for_user(self, user_uuid: UUID, role: str) -> TokenPair:
        token_pair = await generate_token_pair(user_uuid, role)
        token_info = {"user_uuid": user_uuid, "token": token_pair.refresh_token}
        await self.refresh_token_repo.create(token_info)
        return token_pair

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        user = await self.user_repo.get_by_id(str(user_id))
        if not user:
            return None
        return user

    async def create_user(self, form_data: UserSignupForm):
        existing_user = await self.user_repo.find_by_email(form_data.email)
        if existing_user:
            raise UserEmailAlreadyExists
        hashed_password = hash_password(form_data.password.get_secret_value())
        user_data = UserToDB(**form_data.model_dump(), password_hash=hashed_password, role="user")
        new_user = await self.user_repo.create(user_data.model_dump())
        return await self.get_token_pair_for_user(user_uuid=new_user.uuid, role=new_user.role)

    async def authenticate_user(self, form_data: UserLoginForm):
        user = await self.user_repo.find_by_email(form_data.email)
        if not user:
            user = await self.user_repo.find_by_phone(form_data.email)
        if not user or not verify_password(form_data.password.get_secret_value(), user.password_hash):
            raise InvalidCredentials
        return await self.get_token_pair_for_user(user_uuid=user.uuid, role=user.role)

    async def update_user_password(self, user_id: UUID, new_password: str) -> None:
        hashed_password = hash_password(new_password)
        await self.user_repo.update_password(user_id=str(user_id), new_password=hashed_password)

    async def delete_user(self, user_id: UUID) -> None:
        await self.user_repo.delete(str(user_id))

    async def refresh_access_token(self, refresh_token: str) -> TokenPair:
        try:
            user_uuid, role = await get_user_id_from_token(refresh_token)
        except TokenExpired:
            raise RefreshTokenExpired

        refresh_token_session = await self.refresh_token_repo.get_refresh_token_by_token(token=refresh_token)
        if not refresh_token_session:
            raise RefreshTokenNotFound
        if not refresh_token_session.is_active:
            raise RefreshTokenNotActive

        token_pair = await self.get_token_pair_for_user(user_uuid, role)
        return token_pair

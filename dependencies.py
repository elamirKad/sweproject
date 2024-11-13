from fastapi import Depends

from database import get_session
from domains.user.repository import UserRepository
from domains.user.schemas import JWTPayload
from exceptions.user import UserNotFound
from models import User
from utils.tokens import JWTBearer, decode_user_jwt


async def get_current_user_token_payload(
    access_token: str = Depends(JWTBearer()),
) -> JWTPayload:
    """Return current user."""
    payload = await decode_user_jwt(access_token)
    return payload


async def get_current_user(
    payload: JWTPayload = Depends(get_current_user_token_payload),
) -> User:
    async with get_session() as db_session:
        user_repository = UserRepository(db_session)
        user_uuid = payload.user_uuid
        user = await user_repository.get_by_id(str(user_uuid))
    if not user or user.deleted_at:  # type: ignore
        raise UserNotFound
    return user

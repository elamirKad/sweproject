from datetime import datetime, timedelta
from typing import Tuple, cast
from uuid import UUID

import jwt
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger

from config import settings
from domains.user.exceptions import InvalidToken, TokenExpired
from domains.user.schemas import JWTPayload, TokenPair


class JWTBearer(HTTPBearer):
    """Parse Berarer token."""

    def __init__(self, auto_error: bool = True) -> None:
        """Initialize JWT Bearer class."""
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> str:
        """Check auth scheme."""
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme")
            return credentials.credentials
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code")


async def decode_jwt(token: str) -> dict:
    try:
        decoded = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": True, "verify_iat": True},
        )
        return decoded
    except jwt.ExpiredSignatureError:
        raise TokenExpired
    except jwt.InvalidTokenError:
        raise InvalidToken
    except Exception:
        raise InvalidToken


async def decode_user_jwt(token: str):
    try:
        decoded_payload = await decode_jwt(token)
        payload = JWTPayload(
            user_uuid=UUID(decoded_payload["sub"]),
            role=decoded_payload["role"],
            expires_at=datetime.fromtimestamp(decoded_payload["exp"]),
            issued_at=datetime.fromtimestamp(decoded_payload["iat"]),
            token_type=decoded_payload["type"],
        )
    except Exception as e:
        logger.error(e)
        raise InvalidToken
    return payload


async def encode_jwt(
    payload: dict,
    private_key: str = settings.SECRET_KEY,
    algorithm: str = settings.ALGORITHM,
    expire_minutes: int = settings.ACCESS_TOKEN_LIFETIME_MINUTES,
    expire_timedelta: timedelta | None = None,
) -> str:
    current_time = datetime.now()
    if expire_timedelta:
        expires_at = current_time + expire_timedelta
    else:
        expires_at = current_time + timedelta(minutes=expire_minutes)

    payload.update(expires_at=expires_at)
    payload.update(issued_at=current_time)

    to_encode = JWTPayload(**payload).to_jwt_payload

    encoded = jwt.encode(
        to_encode,
        private_key,
        algorithm=algorithm,
    )
    return encoded


async def generate_token_pair(user_uuid: UUID, role: str) -> TokenPair:
    """Генерация пары токенов для пользователя"""

    access_payload = {"user_uuid": user_uuid, "role": role}

    refresh_payload = {"user_uuid": user_uuid, "role": role}

    access_token = await encode_jwt(
        payload=access_payload,
        expire_timedelta=timedelta(minutes=settings.ACCESS_TOKEN_LIFETIME_MINUTES),
    )

    refresh_token = await encode_jwt(
        payload=refresh_payload,
        expire_timedelta=timedelta(days=settings.REFRESH_TOKEN_LIFETIME_DAYS),
    )

    return TokenPair(access_token=access_token, refresh_token=refresh_token)


async def get_user_id_from_token(token: str) -> Tuple[UUID, str]:
    """Получение идентификатора пользователя из токена. Проверка на валидность токена"""

    payload = await decode_user_jwt(token)
    user_uuid = cast(UUID, payload.user_uuid)
    role = str(payload.role)
    return user_uuid, role

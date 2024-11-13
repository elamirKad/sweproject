from fastapi import APIRouter, Depends

from config import settings
from dependencies import get_current_user
from services.user import get_user_service
from shared.exceptions import ServerException, get_exception_responses
from exceptions.user import (
    IncorrectPasswordChars,
    IncorrectPasswordLength,
    InvalidCredentials,
    InvalidToken,
    PasswordIsWeak,
    PhoneNotParsable,
    PhoneNotValid,
    RefreshTokenExpired,
    RefreshTokenNotActive,
    RefreshTokenNotFound,
    TokenDecodeError,
    UserEmailAlreadyExists,
    UserNotFound,
    UserPhoneAlreadyExists,
)
from schemas.user import (
    RefreshToken,
    TokenPair,
    UserInfo,
    UserLoginForm,
    UserSignupForm,
)

router = APIRouter(prefix="/user", tags=["user"])


@router.post(
    "/signup",
    response_model=TokenPair,
    name="Signup user",
    description="Register a new user",
    responses=get_exception_responses(
        ServerException,
        IncorrectPasswordLength,
        IncorrectPasswordChars,
        PasswordIsWeak,
        UserPhoneAlreadyExists,
        UserEmailAlreadyExists,
        PhoneNotValid,
        PhoneNotParsable,
    ),
)
async def signup_user(body: UserSignupForm) -> TokenPair:
    async with get_user_service() as service:
        return await service.create_user(body)


@router.post(
    "/login",
    response_model=TokenPair,
    name="Login user",
    description="Login user to the system",
    responses=get_exception_responses(ServerException, InvalidCredentials, UserNotFound),
)
async def login_user(
    body: UserLoginForm,
) -> TokenPair:
    async with get_user_service() as service:
        return await service.authenticate_user(body)


@router.post(
    "/refresh/",
    response_model=TokenPair,
    name="Refresh token",
    description="Refresh access_token and refresh_token using refresh_token. "
    f"(Access_token lifetime {settings.ACCESS_TOKEN_LIFETIME_MINUTES} minutes.)",
    responses=get_exception_responses(
        RefreshTokenExpired,
        RefreshTokenNotFound,
        RefreshTokenNotActive,
        InvalidToken,
        TokenDecodeError,
    ),
)
async def refresh_token(refresh: RefreshToken) -> TokenPair:
    async with get_user_service() as service:
        return await service.refresh_access_token(refresh.refresh_token)


@router.get(
    "/me",
    response_model=UserInfo,
    name="Get current user",
    description="Get current user",
    responses=get_exception_responses(
        ServerException,
        UserNotFound,
    ),
)
async def get_user(
    user: UserInfo = Depends(get_current_user),
) -> UserInfo:
    return UserInfo.model_validate(user)

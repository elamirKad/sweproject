from starlette import status

from shared.exceptions import BaseHTTPException


class TokenDecodeError(BaseHTTPException):  # type: ignore
    http_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    user_message = "JWT decode error"
    detail = "Error occurred while decoding JWT"


class TokenExpired(BaseHTTPException):  # type: ignore
    http_code = status.HTTP_401_UNAUTHORIZED
    user_message = "Token expired"
    detail = "Token expired"


class InvalidToken(BaseHTTPException):  # type: ignore
    http_code = status.HTTP_401_UNAUTHORIZED
    user_message = "Invalid token"
    detail = "Invalid token"


class RefreshTokenExpired(BaseHTTPException):  # type: ignore
    http_code = status.HTTP_401_UNAUTHORIZED
    user_message = "Сессия истекла"
    detail = "Refresh token expired"


class RefreshTokenNotFound(BaseHTTPException):  # type: ignore
    http_code = status.HTTP_401_UNAUTHORIZED
    user_message = "Refresh token not found"
    detail = "Refresh token not found"


class RefreshTokenNotActive(BaseHTTPException):  # type: ignore
    http_code = status.HTTP_401_UNAUTHORIZED
    user_message = "Сессия заблокирована"
    detail = "Refresh token not active"


class IncorrectPasswordLength(BaseHTTPException):  # type: ignore
    http_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    user_message = "Неправильная длина пароля"


class IncorrectPasswordChars(BaseHTTPException):  # type: ignore
    http_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    user_message = "Пароль содержит недопустимые символы"


class PasswordIsWeak(BaseHTTPException):  # type: ignore
    http_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    user_message = "Слишком слабый пароль"


class InvalidCredentials(BaseHTTPException):  # type: ignore
    http_code = status.HTTP_401_UNAUTHORIZED
    user_message = "Неверные учетные данные"


class UserNotFound(BaseHTTPException):  # type: ignore
    http_code = status.HTTP_404_NOT_FOUND
    user_message = "Пользователь не найден"


class UserEmailAlreadyExists(BaseHTTPException):
    http_code = status.HTTP_400_BAD_REQUEST
    user_message = "Пользователь с данным email уже существует"


class UserPhoneAlreadyExists(BaseHTTPException):
    http_code = status.HTTP_400_BAD_REQUEST
    user_message = "Пользователь с данным номером телефона уже существует"


class AuthorizationException(BaseHTTPException):
    http_code = status.HTTP_403_FORBIDDEN
    user_message = "У вас недостаточно прав на данные действия"


class PhoneNotValid(BaseHTTPException):  # type: ignore
    http_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    user_message = "Неверный формат телефона"
    detail = "Phone number is not valid due to wrong format"


class PhoneNotParsable(BaseHTTPException):  # type: ignore
    http_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    user_message = "Не удалось распарсить телефон"
    detail = "Error occurred while parsing phone number"

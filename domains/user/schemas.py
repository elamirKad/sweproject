import datetime as dt
from datetime import datetime
from string import ascii_letters, ascii_lowercase, ascii_uppercase, digits, punctuation
from typing import Annotated, Any, ClassVar, Dict, Optional, cast
from uuid import UUID

import phonenumbers
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    SecretStr,
    StringConstraints,
    field_validator,
)

from domains.user.exceptions import (
    IncorrectPasswordChars,
    IncorrectPasswordLength,
    PasswordIsWeak,
    PhoneNotParsable,
    PhoneNotValid,
)

NameStr = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=2,
        max_length=128,
        # Регулярное выражение для имени на любом языке Unicode. Может содержать ". -'`"
        pattern=r"^\p{L}[\p{L}\p{M}\. -`']*$",
    ),
]


class JWTToken(BaseModel):  # type: ignore
    access_token: str = Field(..., description="JWT токен пользователя")


class RefreshToken(BaseModel):  # type: ignore
    refresh_token: str = Field(..., description="Рефреш токен, необходимый для обновления access_token")


class AccessToken(BaseModel):  # type: ignore
    access_token: str = Field(
        ...,
        description="JWT пользователя, предназначенный для доступа к ресурсам системы",
    )


class JWTPayload(BaseModel):  # type: ignore
    user_uuid: UUID = Field(..., description="Идентификатор пользователя", alias="sub")
    role: str = Field(..., description="Роль пользователя")
    expires_at: datetime = Field(..., description="Время истечения токена", alias="exp")
    issued_at: datetime = Field(..., description="Время выдачи токена", alias="iat")
    token_type: str = Field("user", description="Тип токена", alias="type")

    @field_validator("token_type")
    @classmethod
    def validate_token_type(cls, value):
        if value != "user":
            raise ValueError("Invalid token type")
        return value

    @property
    def to_jwt_payload(self) -> Dict[str, Any]:
        payload = {
            "sub": str(self.user_uuid),
            "exp": int(self.expires_at.timestamp()),
            "iat": int(self.issued_at.timestamp()),
            "type": self.token_type,
            "role": self.role,
        }
        return payload

    class Config:
        from_attributes = True
        populate_by_name = True


class UserPassword(BaseModel):  # type: ignore
    min_length: ClassVar[int] = 8
    max_length: ClassVar[int] = 16
    valid_chars: ClassVar[str] = ascii_letters + digits + punctuation

    password: SecretStr = Field(..., description="Пароль пользователя", examples=["Password123@"])

    @field_validator("password", mode="before")
    @classmethod
    def validate_and_format_password(cls, password):  # type: ignore
        """
        Валидирует и форматирует переданный пароль.
        Требования к паролю:
          - Длина от 8 до 16 символов
          - Строчные и заглавные буквы латинского алфавита
          - Цифры от 0 до 9
          - Специальные символы !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
        """
        if isinstance(password, str):
            password = password.strip()

            if len(password) < cls.min_length or len(password) > cls.max_length:
                raise IncorrectPasswordLength

            has_upper = False
            has_lower = False
            has_digit = False
            has_special_char = False

            for char in password:
                if char in ascii_uppercase:
                    has_upper = True
                elif char in ascii_lowercase:
                    has_lower = True
                elif char in digits:
                    has_digit = True
                elif char in punctuation:
                    has_special_char = True
                elif char not in cls.valid_chars:
                    raise IncorrectPasswordChars

            if not all([has_upper, has_lower, has_digit, has_special_char]):
                raise PasswordIsWeak

            return password
        return password


class TokenPair(BaseModel):  # type: ignore
    access_token: str = Field(
        ...,
        description="JWT пользователя, предназначенный для доступа к ресурсам системы",
    )
    refresh_token: str = Field(..., description="JWT пользователя, предназначенный для обновления access_token")


class TokenVerificationResponse(BaseModel):  # type: ignore
    is_valid: bool = Field(..., description="Валидность токена")


class EmailBase(BaseModel):  # type: ignore
    email: Optional[EmailStr] = Field(None, description="E-mail пользователя", max_length=256)


class PhoneBase(BaseModel):  # type: ignore
    phone: Optional[str] = Field(
        None,
        description="Телефон пользователя",
        max_length=20,
        min_length=3,
        examples=["+79001234567"],
    )

    @field_validator("phone", mode="before")
    @classmethod
    def validate_and_format_phone_number(cls, phone: Optional[str]) -> Optional[str]:
        """Валидирует и форматирует номер телефона в международный формат E164"""
        if phone is None:
            return phone

        try:
            if phone.startswith("8") or phone.startswith("7"):
                phone = "+7" + phone[1:]
            parsed_phone = phonenumbers.parse(phone)
            if not phonenumbers.is_valid_number(parsed_phone):
                raise PhoneNotValid

            # Форматирование номера телефона в международный формат
            return cast(
                str,
                phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.E164),
            )
        except phonenumbers.NumberParseException:
            raise PhoneNotParsable


class UserBase(EmailBase, PhoneBase):  # type: ignore
    first_name: NameStr = Field(..., description="Имя пользователя", examples=["Имя"])
    last_name: NameStr = Field(..., description="Фамилия пользователя", examples=["Фамилия"])
    middle_name: Optional[NameStr] = Field(None, description="Отчество пользователя", examples=["Отчество"])


class UserToDB(UserBase):
    role: str = Field(..., description="Роль пользователя")
    password_hash: bytes = Field(..., description="Хэш пароля")


class UserSignupForm(UserBase, UserPassword):
    pass


class UserLoginForm(PhoneBase, EmailBase, UserPassword):
    pass


class UserInfo(UserBase):
    uuid: UUID = Field(..., description="UUID пользователя")
    role: str = Field(..., description="Роль пользователя")
    created_at: dt.datetime = Field(..., description="Дата создания пользователя")
    updated_at: Optional[dt.datetime] = Field(None, description="Дата последнего обновления пользователя")
    deleted_at: Optional[dt.datetime] = Field(None, description="Дата удаления пользователя")

    class Config:
        from_attributes = True

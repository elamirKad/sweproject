from typing import cast

import bcrypt

from config import settings


def generate_salt() -> bytes:
    """Генерация соли для хеширования пароля"""
    return cast(bytes, bcrypt.gensalt(settings.PASSWORD_SALT_ROUNDS))


def hash_password(password: str) -> bytes:
    """Хеширование пароля

    :param password: Пароль
    :return: Хеш пароля
    """
    salt = generate_salt()
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
    return cast(bytes, hashed_password)


def verify_password(password: str, hashed_password: bytes) -> bool:
    """Проверка пароля

    :param password: Введенный пароль
    :param hashed_password: Хеш пароля из базы данных
    :return: True, если пароль верный, иначе False
    """
    return cast(bool, bcrypt.checkpw(password.encode("utf-8"), hashed_password))

from http import HTTPStatus
from typing import Any, Optional, Type

import pydantic
from fastapi import HTTPException
from pydantic import BaseModel, Field


class BaseError(BaseModel):  # type: ignore
    """Pydantic модель, описывающая BaseHTTPException json ответ"""

    detail: Any
    user_message: str
    type: Optional[str] = Field("BaseError", description="Exception class name")


class BaseHTTPException(HTTPException):  # type: ignore
    """Класс, предназначенный для создания исключений в системе"""

    http_code: int = 400
    detail: Any = "Error occurred"
    user_message: str = "Unexpected error"
    type: str = "BaseHTTPException"

    def __init__(
        self,
        detail: Any = None,
        user_message: Optional[str] = None,
        status_code: Optional[int] = None,
        exc_type: Optional[str] = None,
    ):
        self.user_message = user_message or self.user_message
        self.type = exc_type or self.__class__.__name__
        super().__init__(status_code=status_code or self.http_code, detail=detail or self.detail)

    @property
    def response_model(self):  # type: ignore
        """Property для корректного отображения исключений в ответах API"""
        model = pydantic.create_model(
            f"{self.__class__.__name__}",
            detail=(str, self.detail),
            user_message=(str, self.user_message),
            type=(str, self.__class__.__name__),
        )

        response = {
            self.http_code: {
                "description": HTTPStatus(self.http_code).phrase,
                "model": BaseError,
                "content": {
                    "application/json": {
                        "examples": {
                            model.__name__: {
                                "summary": model.__name__,
                                "value": model().model_dump(),
                            }
                        }
                    }
                },
            }
        }
        return response


def get_exception_responses(*args: Type[BaseHTTPException | Any]) -> dict:  # type: ignore
    """Функция для добавления классов BaseHTTPException в ответы API"""
    responses = dict()  # type: ignore
    for cls in args:
        response = cls().response_model
        http_code = next(iter(response))
        if http_code in responses:
            responses[http_code]["content"]["application/json"]["examples"].update(
                response[http_code]["content"]["application/json"]["examples"]
            )
        else:
            responses.update(response)
    return responses


class ServerException(BaseHTTPException):
    """Класс исключения для ошибок сервера"""

    http_code = 500
    detail = "Internal server error"
    user_message = "Ошибка сервера"

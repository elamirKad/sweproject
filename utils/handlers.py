from fastapi import Request
from starlette.responses import JSONResponse

from domains.base_exception import BaseError, BaseHTTPException


async def base_http_exception_handler(request: Request, exc: BaseHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content=BaseError(detail=exc.detail, user_message=exc.user_message, type=exc.type).model_dump(),
    )

import logging

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    error_name = getattr(exc, "error", exc.__class__.__name__)
    message = getattr(exc, "message", exc.detail)

    logger.error(
        "%s %s - %s: %s",
        request.method,
        request.url.path,
        error_name,
        message,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": error_name,
            "message": message,
        },
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.exception(
        "Erro interno em %s %s",
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "Ocorreu um erro interno no servidor.",
        },
    )

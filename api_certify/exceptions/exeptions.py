from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from api_certify.schemas.responses import ErrorResponse


async def http_exception_handler(request: Request, exc: HTTPException):
    error_content = ErrorResponse(
        success=False,
        message=exc.detail,
        error_code=f'HTTP_{exc.status_code}',
        details=f'Path: {request.url.path}',
    )
    return JSONResponse(
        status_code=exc.status_code, content=error_content.model_dump()
    )


async def validation_exception_handler(request: Request, exc: Exception):
    error_content = ErrorResponse(
        success=False,
        message='Validation error',
        error_code='VALIDATION_ERROR',
        details=str(exc),
    )
    return JSONResponse(status_code=422, content=error_content.model_dump())

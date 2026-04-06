import pytest
from fastapi import HTTPException
from starlette.requests import Request

from api_certify.exceptions.exeptions import (
    http_exception_handler,
    validation_exception_handler,
    QuotaNotEnoughException,
)


def create_fake_request():
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/test-path",
        "headers": [],
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_http_exception_handler():

    request = create_fake_request()
    exc = HTTPException(status_code=400, detail="Erro")

    response = await http_exception_handler(request, exc)

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_validation_exception_handler():

    request = create_fake_request()
    exc = Exception("validation failed")

    response = await validation_exception_handler(request, exc)

    assert response.status_code == 422


def test_quota_not_enough_exception():

    exc = QuotaNotEnoughException()

    assert exc.status_code == 403
    assert exc.message == "quota not enough"
    assert exc.content() == {"error_msg": "quota not enough"}

import json

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from api_certify.exceptions import QuotaNotEnoughException
from api_certify.exceptions.handlers import (
    generic_exception_handler,
    http_exception_handler,
)


def create_fake_request() -> Request:
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
    exc = HTTPException(
        status_code=400,
        detail="Requisição inválida",
    )

    response = await http_exception_handler(request, exc)

    assert response.status_code == 400

    body = json.loads(response.body)
    assert body == {
        "error": "HTTPException",
        "message": "Requisição inválida",
    }


@pytest.mark.asyncio
async def test_generic_exception_handler():
    request = create_fake_request()
    exc = Exception("validation failed")

    response = await generic_exception_handler(request, exc)

    assert response.status_code == 500

    body = json.loads(response.body)
    assert body == {
        "error": "InternalServerError",
        "message": "Ocorreu um erro interno no servidor.",
    }


def test_quota_not_enough_exception():
    exc = QuotaNotEnoughException()

    assert exc.status_code == 403
    assert exc.error == "QuotaNotEnoughException"
    assert exc.message == "Cota insuficiente."
    assert exc.detail == "Cota insuficiente."

import pytest
from unittest.mock import AsyncMock
from fastapi import HTTPException

from api_certify.models.auth_model import (
    AuthUser,
    AuthUserLogin,
    AuthUserReponse,
    Role,
)


@pytest.mark.asyncio
async def test_signup_success(auth_service, auth_repository_mock):

    payload = AuthUser(
        fullname="Teste User",
        email="teste@example.com",
        password="SenhaSegura123!",
        role=Role.USER,
    )

    auth_repository_mock.create = AsyncMock(
        return_value=AuthUserReponse(
            _id="1",
            fullname=payload.fullname,
            email=payload.email,
            role=payload.role,
            status="pending",
        )
    )

    result = await auth_service.create_auth_user(payload)

    assert result.email == payload.email
    assert result.fullname == payload.fullname


@pytest.mark.asyncio
async def test_login_success(auth_service, auth_repository_mock):

    payload = AuthUserLogin(
        email="teste@example.com",
        password="SenhaSegura123!",
    )

    auth_repository_mock.login = AsyncMock(
        return_value=AuthUserReponse(
            _id="1",
            fullname="Teste User",
            email="teste@example.com",
            role=Role.USER,
            status="pending",
        )
    )

    result = await auth_service.login_auth(payload)

    assert result["token_type"] == "bearer"
    assert "access_token" in result


@pytest.mark.asyncio
async def test_signup_duplicate_email(auth_service, auth_repository_mock):

    payload = AuthUser(
        fullname="Outro User",
        email="teste@example.com",
        password="SenhaSegura123!",
        role=Role.USER,
    )

    auth_repository_mock.create = AsyncMock(
        side_effect=HTTPException(status_code=409, detail="Email already exists")
    )

    with pytest.raises(HTTPException):
        await auth_service.create_auth_user(payload)

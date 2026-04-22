import pytest
from unittest.mock import AsyncMock
from fastapi import HTTPException

from api_certify.models.auth_model import (
    AuthUser,
    AuthUserLogin,
    AuthUserReponse,
    UpdateUserSchema,
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


@pytest.mark.asyncio
async def test_update_user_success(auth_service, auth_repository_mock):

    update_data = UpdateUserSchema(fullname="Nome Atualizado")

    auth_repository_mock.update = AsyncMock(
        return_value=AuthUserReponse(
            _id="1",
            fullname="Nome Atualizado",
            email="teste@example.com",
            role=Role.USER,
            status="pending",
        )
    )

    result = await auth_service.update_user("1", update_data, "1")

    assert result.fullname == "Nome Atualizado"


@pytest.mark.asyncio
async def test_update_user_forbidden(auth_service):

    update_data = UpdateUserSchema(fullname="Hacker")

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.update_user("1", update_data, "outro-user")

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_update_user_email_conflict(auth_service, auth_repository_mock):

    update_data = UpdateUserSchema(email="existente@example.com")

    auth_repository_mock.update = AsyncMock(
        side_effect=Exception("Email já cadastrado")
    )

    with pytest.raises(Exception, match="Email já cadastrado"):
        await auth_service.update_user("1", update_data, "1")

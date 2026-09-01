from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from api_certify.core.security import create_access_token
from api_certify.dependencies import (
    get_auth_repository,
    get_auth_service,
    get_certificate_repository,
    get_certificate_service,
    get_event_repository,
    get_event_service,
    get_refresh_token_repository,
    get_current_user,
    require_role,
)
from api_certify.repositories.auth_repository import AuthRepository
from api_certify.repositories.certificate_repository import CertificateRepository
from api_certify.service.auth_service import AuthService
from api_certify.service.certificate_service import CertificateService

from api_certify.service.auth_service import AuthService
from api_certify.service.certificate_service import CertificateService
from api_certify.service.event_service import EventService
from api_certify.repositories.auth_repository import AuthRepository
from api_certify.repositories.certificate_repository import CertificateRepository
from api_certify.repositories.event_repository import EventRepository
from api_certify.repositories.refresh_token_repository import RefreshTokenRepository


@pytest.fixture
def fake_database():
    return MagicMock()


@pytest.mark.asyncio
async def test_get_auth_repository(mocker, fake_database):

    mocker.patch(
        "api_certify.dependencies.db_mongo.get_database",
        new=AsyncMock(return_value=fake_database),
    )

    repo = await get_auth_repository()

    assert isinstance(repo, AuthRepository)


@pytest.mark.asyncio
async def test_get_certificate_repository(mocker, fake_database):

    mocker.patch(
        "api_certify.dependencies.db_mongo.get_database",
        new=AsyncMock(return_value=fake_database),
    )

    repo = await get_certificate_repository()

    assert isinstance(repo, CertificateRepository)


def test_get_auth_service():

    fake_repo = MagicMock()
    fake_refresh_repo = MagicMock()

    service = get_auth_service(fake_repo, fake_refresh_repo)

    assert isinstance(service, AuthService)


@pytest.mark.asyncio
async def test_get_refresh_token_repository(mocker, fake_database):

    mocker.patch(
        "api_certify.dependencies.db_mongo.get_database",
        new=AsyncMock(return_value=fake_database),
    )

    repo = await get_refresh_token_repository()

    assert isinstance(repo, RefreshTokenRepository)


def test_get_certificate_service():

    fake_cert_repo = MagicMock()
    fake_auth_repo = MagicMock()
    fake_event_repo = MagicMock()

    service = get_certificate_service(fake_cert_repo, fake_auth_repo, fake_event_repo)

    assert isinstance(service, CertificateService)


@pytest.mark.asyncio
async def test_get_event_repository(mocker, fake_database):

    mocker.patch(
        "api_certify.dependencies.db_mongo.get_database",
        new=AsyncMock(return_value=fake_database),
    )

    repo = await get_event_repository()

    assert isinstance(repo, EventRepository)


def test_get_event_service():

    fake_repo = MagicMock()

    service = get_event_service(fake_repo)

    assert isinstance(service, EventService)


@pytest.mark.asyncio
async def test_get_current_user_valid_token():
    token = create_access_token(
        {
            "sub": "123",
            "email": "user@test.com",
            "role": "user",
        }
    )
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    user = await get_current_user(credentials)

    assert user["sub"] == "123"
    assert user["email"] == "user@test.com"


@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid")

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_require_role_allows_empresa():

    checker = require_role("empresa")

    current_user = {
        "sub": "123",
        "email": "empresa@test.com",
        "role": "empresa",
    }

    result = await checker(current_user=current_user)

    assert result == current_user


@pytest.mark.asyncio
async def test_require_role_allows_admin():

    checker = require_role("empresa")

    current_user = {
        "sub": "123",
        "email": "admin@test.com",
        "role": "admin",
    }

    result = await checker(current_user=current_user)

    assert result == current_user


@pytest.mark.asyncio
async def test_require_role_denies_user():

    checker = require_role("empresa")

    current_user = {
        "sub": "123",
        "email": "user@test.com",
        "role": "user",
    }

    with pytest.raises(HTTPException) as exc_info:
        await checker(current_user=current_user)

    assert exc_info.value.status_code == 403
    assert (
        exc_info.value.detail == "Acesso negado. Permissão insuficiente para esta ação."
    )

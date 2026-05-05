import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from api_certify.core.security import create_access_token
from api_certify.dependencies import (
    get_auth_repository,
    get_auth_service,
    get_certificate_repository,
    get_certificate_service,
    get_current_user,
)

from api_certify.service.auth_service import AuthService
from api_certify.service.certificate_service import CertificateService
from api_certify.repositories.auth_repository import AuthRepository
from api_certify.repositories.certificate_repository import CertificateRepository


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

    service = get_auth_service(fake_repo)

    assert isinstance(service, AuthService)


def test_get_certificate_service():

    fake_cert_repo = MagicMock()
    fake_auth_repo = MagicMock()

    service = get_certificate_service(fake_cert_repo, fake_auth_repo)

    assert isinstance(service, CertificateService)


@pytest.mark.asyncio
async def test_get_current_user_valid_token():
    token = create_access_token({"sub": "123", "email": "user@test.com"})
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

import pytest
from unittest.mock import AsyncMock, MagicMock

from api_certify.dependencies import (
    get_auth_repository,
    get_auth_service,
    get_certificate_repository,
    get_certificate_service,
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

import pytest_asyncio
from unittest.mock import AsyncMock
from httpx import AsyncClient, ASGITransport

from api_certify.main import app
from api_certify.service.auth_service import AuthService
from api_certify.service.certificate_service import CertificateService
from api_certify.dependencies import (
    get_auth_repository,
    get_certificate_repository,
)


# -----------------------------
# Repository Mocks
# -----------------------------


@pytest_asyncio.fixture
async def auth_repository_mock():
    repo = AsyncMock()

    repo.isExistAuth.return_value = False
    repo.create_auth_user.return_value = None
    repo.login_auth.return_value = {"access_token": "fake-token"}

    return repo


@pytest_asyncio.fixture
async def certificate_repository_mock():
    repo = AsyncMock()

    repo.find_existing_certificate.return_value = None
    repo.create.return_value = None
    repo.get_many_certificates.return_value = []
    repo.get_certificate.return_value = None

    return repo


# -----------------------------
# Services
# -----------------------------


@pytest_asyncio.fixture
async def auth_service(auth_repository_mock):
    return AuthService(auth_repository_mock)


@pytest_asyncio.fixture
async def certificate_service(certificate_repository_mock, auth_repository_mock):
    return CertificateService(certificate_repository_mock, auth_repository_mock)


# -----------------------------
# HTTP Test Client
# -----------------------------


@pytest_asyncio.fixture
async def async_client(auth_service, certificate_service):

    app.dependency_overrides[get_auth_repository] = lambda: auth_service
    app.dependency_overrides[get_certificate_repository] = lambda: certificate_service

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()

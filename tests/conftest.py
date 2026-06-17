from unittest.mock import AsyncMock

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from api_certify.dependencies import get_auth_repository, get_certificate_repository
from api_certify.main import app
from api_certify.models.auth_model import AuthUserReponse, Role
from api_certify.service.auth_service import AuthService
from api_certify.service.certificate_service import CertificateService

# -----------------------------
# Repository Mocks
# -----------------------------


@pytest_asyncio.fixture
async def auth_repository_mock():
    repo = AsyncMock()

    repo.isExistAuth.return_value = False
    repo.create_auth_user.return_value = None
    repo.login_auth.return_value = {"access_token": "fake-token"}
    repo.get_user_by_id.return_value = AuthUserReponse(
        _id="1",
        fullname="Teste User",
        email="teste@example.com",
        role=Role.USER,
        status="available",
    )

    return repo


@pytest_asyncio.fixture
async def refresh_token_repository_mock():
    repo = AsyncMock()

    repo.create.return_value = {}
    repo.find_valid_token.return_value = None
    repo.revoke.return_value = True
    repo.revoke_all_for_user.return_value = 0

    return repo


@pytest_asyncio.fixture
async def certificate_repository_mock():
    repo = AsyncMock()

    repo.find_existing_certificate.return_value = None
    repo.create.return_value = None
    repo.get_many_certificates.return_value = []
    repo.get_certificate.return_value = None

    return repo


@pytest_asyncio.fixture
async def event_repository_mock():
    repo = AsyncMock()

    repo.exists.return_value = True
    repo.create.return_value = None
    repo.find_by_id.return_value = None

    return repo


# -----------------------------
# Services
# -----------------------------


@pytest_asyncio.fixture
async def auth_service(auth_repository_mock, refresh_token_repository_mock):
    return AuthService(auth_repository_mock, refresh_token_repository_mock)


@pytest_asyncio.fixture
async def certificate_service(
    certificate_repository_mock, auth_repository_mock, event_repository_mock
):
    return CertificateService(
        certificate_repository_mock, auth_repository_mock, event_repository_mock
    )


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

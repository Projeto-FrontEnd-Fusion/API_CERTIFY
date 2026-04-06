import pytest_asyncio
from unittest.mock import AsyncMock

from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager

from api_certify.main import app
from api_certify.service.auth_service import AuthService
from api_certify.service.certificate_service import CertificateService
from api_certify.dependencies import (
    get_auth_repository,
    get_certificate_repository,
)


# ---------------------------
# Mock Factory
# ---------------------------


def create_async_mock(**methods) -> AsyncMock:
    """Cria AsyncMock configurado dinamicamente"""
    mock = AsyncMock()
    for method, value in methods.items():
        getattr(mock, method).return_value = value
    return mock


# ---------------------------
# Repository Mocks
# ---------------------------


@pytest_asyncio.fixture
def auth_repository_mock() -> AsyncMock:
    return create_async_mock(
        isExistAuth=False,
        create_auth_user=None,
        login_auth={"access_token": "fake-token"},
    )


@pytest_asyncio.fixture
def certificate_repository_mock() -> AsyncMock:
    return create_async_mock(
        find_existing_certificate=None,
        create=None,
        get_many_certificates=[],
        get_certificate=None,
    )


# ---------------------------
# Services
# ---------------------------


@pytest_asyncio.fixture
def auth_service(auth_repository_mock: AsyncMock) -> AuthService:
    return AuthService(auth_repository_mock)


@pytest_asyncio.fixture
def certificate_service(
    certificate_repository_mock: AsyncMock,
    auth_repository_mock: AsyncMock,
) -> CertificateService:
    return CertificateService(
        certificate_repository_mock,
        auth_repository_mock,
    )


# ---------------------------
# HTTP Client
# ---------------------------


@pytest_asyncio.fixture
async def async_client(
    auth_service: AuthService,
    certificate_service: CertificateService,
):
    """Cliente HTTP assíncrono configurado para testes"""

    app.dependency_overrides.update(
        {
            get_auth_repository: lambda: auth_service,
            get_certificate_repository: lambda: certificate_service,
        }
    )

    transport = ASGITransport(app=app)

    async with LifespanManager(app):
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            yield client

    app.dependency_overrides.clear()

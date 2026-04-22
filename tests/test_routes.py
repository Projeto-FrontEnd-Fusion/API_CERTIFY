import pytest
import pytest_asyncio
from unittest.mock import AsyncMock
from httpx import AsyncClient, ASGITransport

from api_certify.main import app
from api_certify.core.security import create_access_token
from api_certify.dependencies import (
    get_auth_service,
    get_certificate_service,
    get_current_user,
)
from api_certify.service.certificate_service import CertificateService


# ==========================================
# MOCK SERVICES
# ==========================================


@pytest.fixture
def auth_service_mock():
    return AsyncMock()


@pytest.fixture
def certificate_service_mock():
    return AsyncMock(spec=CertificateService)


@pytest.fixture
def fake_current_user():
    return {"sub": "user123", "email": "test@email.com"}


@pytest.fixture
def auth_headers():
    token = create_access_token({"sub": "user123", "email": "test@email.com"})
    return {"Authorization": f"Bearer {token}"}


# ==========================================
# DEPENDENCY OVERRIDE
# ==========================================


@pytest.fixture
def override_dependencies(auth_service_mock, certificate_service_mock, fake_current_user):
    app.dependency_overrides[get_auth_service] = lambda: auth_service_mock
    app.dependency_overrides[get_certificate_service] = lambda: certificate_service_mock
    app.dependency_overrides[get_current_user] = lambda: fake_current_user

    yield

    app.dependency_overrides.clear()


# ==========================================
# CLIENT
# ==========================================


@pytest_asyncio.fixture
async def async_client(override_dependencies):
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client


# ==========================================
# HELPERS
# ==========================================


def get_certificate(body: dict):
    return body.get("data", {}).get("certificate")


def assert_error_response(body: dict, message: str, status_code: int = 404):
    assert body["success"] is False
    assert body["message"] == message
    assert body["error_code"] == f"HTTP_{status_code}"
    assert "details" in body


# ==========================================
# TESTS - AUTH
# ==========================================


@pytest.mark.asyncio
async def test_login_user(async_client, auth_service_mock):

    auth_service_mock.login_auth.return_value = {"access_token": "fake-token"}

    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@email.com",
            "password": "SenhaSegura123!",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"]["access_token"] == "fake-token"


# ==========================================
# TESTS - CERTIFICATE (PROTEGIDAS)
# ==========================================


@pytest.mark.asyncio
async def test_create_certificate(async_client, certificate_service_mock, auth_headers):

    certificate_service_mock.create_participant_certificate.return_value = {
        "id": "cert_123",
        "fullname": "João Silva Santos",
        "event_id": "evt_123",
        "status": "available",
    }

    response = await async_client.post(
        "/api/v1/certificate/user123",
        json={
            "fullname": "João Silva Santos",
            "access_key": "ABC123",
            "event_id": "evt_123",
            "status": "pending",
            "email": "joao@email.com",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201

    certificate = get_certificate(response.json())

    assert certificate is not None
    assert certificate["id"] == "cert_123"


@pytest.mark.asyncio
async def test_get_many_certificates(async_client, certificate_service_mock, auth_headers):

    certificate_service_mock.get_many_certificates.return_value = [{"id": "cert_123"}]

    response = await async_client.get(
        "/api/v1/certificate/users/user123",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert isinstance(body["data"]["certificates"], list)


@pytest.mark.asyncio
async def test_get_certificate_by_id(async_client, certificate_service_mock, auth_headers):

    certificate_service_mock.get_certificate_by_id.return_value = {
        "id": "cert_123",
        "status": "available",
    }

    response = await async_client.get(
        "/api/v1/certificate/cert_123",
        headers=auth_headers,
    )

    assert response.status_code == 200

    certificate = get_certificate(response.json())

    assert certificate is not None
    assert certificate["id"] == "cert_123"


# ==========================================
# TESTS - ROTAS PROTEGIDAS SEM TOKEN
# ==========================================


@pytest_asyncio.fixture
async def async_client_no_auth(auth_service_mock, certificate_service_mock):
    app.dependency_overrides[get_auth_service] = lambda: auth_service_mock
    app.dependency_overrides[get_certificate_service] = lambda: certificate_service_mock

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_certificate_without_token(async_client_no_auth):
    response = await async_client_no_auth.post(
        "/api/v1/certificate/user123",
        json={
            "fullname": "João Silva Santos",
            "access_key": "ABC123",
            "event_id": "evt_123",
            "status": "pending",
            "email": "joao@email.com",
        },
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_certificates_without_token(async_client_no_auth):
    response = await async_client_no_auth.get("/api/v1/certificate/users/user123")

    assert response.status_code == 403


# ==========================================
# TESTS - VALIDAÇÃO PÚBLICA (SEM TOKEN)
# ==========================================


@pytest.mark.asyncio
async def test_validate_certificate_success(async_client, certificate_service_mock):

    certificate_service_mock.validate_certificate.return_value = {
        "participant_name": "João Silva Santos",
        "event_name": "Python Conference",
        "workload": "10",
        "issued_at": "2026-01-01",
        "status": "available",
    }

    response = await async_client.get("/api/v1/certificate/validate/ABC123")

    assert response.status_code == 200

    certificate = get_certificate(response.json())

    assert certificate is not None
    assert "participant_name" in certificate
    assert "event_name" in certificate
    assert "workload" in certificate
    assert "issued_at" in certificate


@pytest.mark.asyncio
async def test_validate_certificate_not_found(async_client, certificate_service_mock):

    certificate_service_mock.validate_certificate.return_value = None

    response = await async_client.get("/api/v1/certificate/validate/INVALID")

    assert response.status_code == 404

    body = response.json()

    assert_error_response(body, "Certificado não encontrado")


@pytest.mark.asyncio
async def test_validate_certificate_invalid_status(
    async_client, certificate_service_mock
):

    certificate_service_mock.validate_certificate.return_value = None

    response = await async_client.get("/api/v1/certificate/validate/ABC123")

    assert response.status_code == 404

    body = response.json()

    assert_error_response(body, "Certificado não encontrado")


@pytest.mark.asyncio
async def test_validate_certificate_case_sensitive(
    async_client, certificate_service_mock
):

    def mock_validate(key):
        if key == "ABC123":
            return {
                "participant_name": "João Silva",
                "status": "available",
            }
        return None

    certificate_service_mock.validate_certificate.side_effect = mock_validate

    response = await async_client.get("/api/v1/certificate/validate/abc123")

    assert response.status_code == 404

    body = response.json()

    assert_error_response(body, "Certificado não encontrado")


@pytest.mark.asyncio
async def test_validate_certificate_public_route(async_client_no_auth):
    response = await async_client_no_auth.get("/api/v1/certificate/validate/ABC123")

    assert response.status_code != 401
    assert response.status_code != 403

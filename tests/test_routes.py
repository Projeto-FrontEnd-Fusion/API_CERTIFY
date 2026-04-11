import pytest
import pytest_asyncio
from unittest.mock import AsyncMock
from httpx import AsyncClient, ASGITransport

from api_certify.main import app
from api_certify.dependencies import (
    get_auth_service,
    get_certificate_service,
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


# ==========================================
# DEPENDENCY OVERRIDE
# ==========================================


@pytest.fixture
def override_dependencies(auth_service_mock, certificate_service_mock):
    app.dependency_overrides[get_auth_service] = lambda: auth_service_mock
    app.dependency_overrides[get_certificate_service] = lambda: certificate_service_mock

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
# TESTS - CERTIFICATE
# ==========================================


@pytest.mark.asyncio
async def test_create_certificate(async_client, certificate_service_mock):

    certificate_service_mock.create_participant_certificate.return_value = {
        "id": "cert_123",
        "fullname": "João Silva Santos",
        "event_id": "evt_123",
        "status": "Emitido",
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
    )

    assert response.status_code == 201

    certificate = get_certificate(response.json())

    assert certificate is not None
    assert certificate["id"] == "cert_123"


@pytest.mark.asyncio
async def test_get_many_certificates(async_client, certificate_service_mock):

    certificate_service_mock.get_many_certificates.return_value = [{"id": "cert_123"}]

    response = await async_client.get("/api/v1/certificate/users/user123")

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert isinstance(body["data"]["certificates"], list)


@pytest.mark.asyncio
async def test_get_certificate_by_id(async_client, certificate_service_mock):

    certificate_service_mock.get_certificate_by_id.return_value = {
        "id": "cert_123",
        "status": "Emitido",
    }

    response = await async_client.get("/api/v1/certificate/cert_123")

    assert response.status_code == 200

    certificate = get_certificate(response.json())

    assert certificate is not None
    assert certificate["id"] == "cert_123"


# ==========================================
# TESTS - VALIDAÇÃO PÚBLICA (TASK #30)
# ==========================================


@pytest.mark.asyncio
async def test_validate_certificate_success(async_client, certificate_service_mock):

    certificate_service_mock.validate_certificate.return_value = {
        "fullname": "João Silva Santos",
        "event_name": "Python Conference",
        "workload": 10,
        "issued_at": "2026-01-01",
        "status": "Emitido",
    }

    response = await async_client.get("/api/v1/certificate/validate/ABC123")

    assert response.status_code == 200

    certificate = get_certificate(response.json())

    assert certificate is not None
    assert certificate["status"] in ["Emitido", "Ativo"]

    assert "fullname" in certificate
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
                "fullname": "João Silva",
                "status": "Emitido",
            }
        return None

    certificate_service_mock.validate_certificate.side_effect = mock_validate

    response = await async_client.get("/api/v1/certificate/validate/abc123")

    assert response.status_code == 404

    body = response.json()

    assert_error_response(body, "Certificado não encontrado")


@pytest.mark.asyncio
async def test_validate_certificate_public_route(async_client):

    response = await async_client.get("/api/v1/certificate/validate/ABC123")

    assert response.status_code != 401

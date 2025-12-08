import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock
from api_certify.main import app
from api_certify.schemas.responses import SucessResponse
from api_certify.models.certificate_model import CreateCertificate
from api_certify.dependencies import get_current_active_user, get_certificate_service

# Mock do usuário logado
fake_user = {
    "_id": "user123",
    "fullname": "Douglas Phelipe",
    "email": "douglas@example.com",
    "role": "user",
    "status": "active"
}

# Mock de certificado
fake_certificate = {
    "fullname": "Douglas Phelipe",
    "access_key": "ABC123",
    "event_id": "evt_987654321",
    "status": "available",
    "email": "douglas@gmail.com"
    }


@pytest.mark.asyncio
async def test_request_certificate():
    payload = {
        "fullname": "Douglas Phelipe",
        "access_key": "ABC123",
        "event_id": "evt_987654321",
        "status": "available",
        "email": "douglas@gmail.com"
    }

    mock_service = AsyncMock()
    mock_service.create_participant_certificate.return_value = fake_certificate

    # Sobrescreve dependências do FastAPI
    app.dependency_overrides[get_current_active_user] = lambda: fake_user
    app.dependency_overrides[get_certificate_service] = lambda: mock_service

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(f"/api/v1/certificate/{fake_user['_id']}", json=payload)

    # Limpa overrides
    app.dependency_overrides = {}

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["certificate"] == fake_certificate
    

@pytest.mark.asyncio
async def test_get_many_certificate():
    mock_service = AsyncMock()
    mock_service.get_many_certificates.return_value = [fake_certificate]

    # Sobrescreve dependências do FastAPI
    app.dependency_overrides[get_current_active_user] = lambda: fake_user
    app.dependency_overrides[get_certificate_service] = lambda: mock_service

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/certificate/users/{fake_user['_id']}")
        
    # Limpa overrides
    app.dependency_overrides = {}

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["certificates"] == [fake_certificate]


@pytest.mark.asyncio
async def test_get_certificate_by_id():
    mock_service = AsyncMock()
    mock_service.get_certificate_by_id.return_value = fake_certificate

    # Sobrescreve dependências do FastAPI
    app.dependency_overrides[get_current_active_user] = lambda: fake_user
    app.dependency_overrides[get_certificate_service] = lambda: mock_service

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/certificate/{fake_user['_id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["certificate"] == fake_certificate
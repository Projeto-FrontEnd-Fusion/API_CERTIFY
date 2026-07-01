from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from api_certify.core.security import create_access_token
from api_certify.dependencies import (
    get_auth_service,
    get_certificate_service,
    get_current_user,
    get_event_service,
)
from api_certify.main import app
from api_certify.service.certificate_service import CertificateService
from api_certify.service.event_service import EventService

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
def event_service_mock():
    return AsyncMock(spec=EventService)


@pytest.fixture
def fake_current_user():
    return {"sub": "user123", "email": "test@email.com", "role": "user"}


@pytest.fixture
def auth_headers():
    token = create_access_token(
        {"sub": "user123", "email": "test@email.com", "role": "user"}
    )
    return {"Authorization": f"Bearer {token}"}


# ==========================================
# DEPENDENCY OVERRIDE
# ==========================================


@pytest.fixture
def override_dependencies(
    auth_service_mock, certificate_service_mock, event_service_mock, fake_current_user
):
    app.dependency_overrides[get_auth_service] = lambda: auth_service_mock
    app.dependency_overrides[get_certificate_service] = lambda: certificate_service_mock
    app.dependency_overrides[get_event_service] = lambda: event_service_mock
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


def assert_error_response(
    body: dict,
    message: str,
    error: str = "HTTPException",
):
    assert body["error"] == error
    assert body["message"] == message


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


@pytest.mark.asyncio
async def test_signup_company_success(async_client, auth_service_mock):

    auth_service_mock.create_company_user.return_value = {
        "_id": "comp_123",
        "razao_social": "Empresa Teste Ltda",
        "cnpj": "12345678000195",
        "email": "contato@empresa.com",
        "phone": "(11) 99999-8888",
        "role": "empresa",
    }

    response = await async_client.post(
        "/api/v1/auth/signup/company",
        json={
            "razao_social": "Empresa Teste Ltda",
            "cnpj": "12.345.678/0001-95",
            "email": "contato@empresa.com",
            "password": "SenhaSegura123!",
            "phone": "(11) 99999-8888",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["success"] is True
    assert body["data"]["auth"]["email"] == "contato@empresa.com"


@pytest.mark.asyncio
async def test_signup_company_cnpj_invalid(async_client, auth_service_mock):

    auth_service_mock.create_company_user.side_effect = Exception("CNPJ inválido")

    response = await async_client.post(
        "/api/v1/auth/signup/company",
        json={
            "razao_social": "Empresa Teste Ltda",
            "cnpj": "11.111.111/1111-11",
            "email": "contato@empresa.com",
            "password": "SenhaSegura123!",
        },
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_signup_company_duplicates(async_client, auth_service_mock):

    # CNPJ duplicate
    auth_service_mock.create_company_user.side_effect = Exception("CNPJ já cadastrado")

    response = await async_client.post(
        "/api/v1/auth/signup/company",
        json={
            "razao_social": "Empresa Teste Ltda",
            "cnpj": "12.345.678/0001-95",
            "email": "contato@empresa.com",
            "password": "SenhaSegura123!",
        },
    )

    assert response.status_code == 409

    # Email duplicate
    auth_service_mock.create_company_user.side_effect = Exception("Email já cadastrado")

    response = await async_client.post(
        "/api/v1/auth/signup/company",
        json={
            "razao_social": "Empresa Teste Ltda",
            "cnpj": "98.765.432/0001-10",
            "email": "contato@empresa.com",
            "password": "SenhaSegura123!",
        },
    )

    assert response.status_code == 409


# ==========================================
# TESTS - CERTIFICATE (PROTEGIDAS)
# ==========================================


@pytest.mark.asyncio
async def test_create_certificate(
    company_client, certificate_service_mock, company_headers
):

    certificate_service_mock.create_participant_certificate.return_value = {
        "id": "cert_123",
        "fullname": "João Silva Santos",
        "event_id": "evt_123",
        "status": "available",
    }

    response = await company_client.post(
        "/api/v1/certificate/user123",
        json={
            "fullname": "João Silva Santos",
            "access_key": "ABC123",
            "event_id": "evt_123",
            "status": "pending",
            "email": "joao@email.com",
        },
        headers=company_headers,
    )

    assert response.status_code == 201

    certificate = get_certificate(response.json())

    assert certificate is not None
    assert certificate["id"] == "cert_123"


@pytest.mark.asyncio
async def test_create_batch_certificates(
    company_client, certificate_service_mock, company_headers
):
    certificate_service_mock.create_batch_certificates.return_value = {
        "total_enviados": 2,
        "criados": 2,
        "duplicados_ignorados": 0,
        "erros": 0,
    }

    response = await company_client.post(
        "/api/v1/certificate/batch",
        json={
            "event_id": "evt_123",
            "participants": [
                {"fullname": "João Silva Santos", "email": "joao@email.com"},
                {"fullname": "Maria Souza", "email": "maria@email.com"},
            ],
        },
        headers=company_headers,
    )

    assert response.status_code == 201
    assert response.json()["data"]["criados"] == 2


@pytest.mark.asyncio
async def test_get_many_certificates(
    async_client,
    certificate_service_mock,
    auth_headers,
):

    certificate_service_mock.get_many_certificates.return_value = {
        "items": [{"id": "cert_123"}],
        "total": 1,
        "page": 1,
        "limit": 20,
        "total_pages": 1,
    }

    response = await async_client.get(
        "/api/v1/certificate/users/user123",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert isinstance(body["data"]["items"], list)
    assert body["data"]["total"] == 1
    assert body["data"]["page"] == 1
    assert body["data"]["limit"] == 20
    assert body["data"]["total_pages"] == 1


@pytest.mark.asyncio
async def test_get_certificate_by_id(
    async_client, certificate_service_mock, auth_headers
):

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
async def async_client_no_auth(
    auth_service_mock, certificate_service_mock, event_service_mock
):
    app.dependency_overrides[get_auth_service] = lambda: auth_service_mock
    app.dependency_overrides[get_certificate_service] = lambda: certificate_service_mock
    app.dependency_overrides[get_event_service] = lambda: event_service_mock

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


# ==========================================
# TESTS - UPDATE USER (PROTEGIDA)
# ==========================================


@pytest.mark.asyncio
async def test_update_user_success(async_client, auth_service_mock, auth_headers):

    auth_service_mock.update_user.return_value = {
        "_id": "user123",
        "fullname": "Nome Atualizado",
        "email": "test@email.com",
        "role": "user",
        "status": "pending",
    }

    response = await async_client.put(
        "/api/v1/auth/user123",
        json={"fullname": "Nome Atualizado"},
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Dados atualizados com sucesso"


@pytest.mark.asyncio
async def test_update_user_not_found(async_client, auth_service_mock, auth_headers):

    auth_service_mock.update_user.side_effect = Exception("Usuário não encontrado")

    response = await async_client.put(
        "/api/v1/auth/user123",
        json={"fullname": "Teste Atualizado"},
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_user_email_conflict(
    async_client, auth_service_mock, auth_headers
):

    auth_service_mock.update_user.side_effect = Exception("Email já cadastrado")

    response = await async_client.put(
        "/api/v1/auth/user123",
        json={"email": "existente@email.com"},
        headers=auth_headers,
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_user_without_token(async_client_no_auth):

    response = await async_client_no_auth.put(
        "/api/v1/auth/user123",
        json={"fullname": "Hacker"},
    )

    assert response.status_code == 403


@pytest.fixture
def fake_company_user():
    return {
        "sub": "company123",
        "email": "empresa@test.com",
        "role": "empresa",
    }


@pytest.fixture
def company_headers():
    token = create_access_token(
        {
            "sub": "company123",
            "email": "empresa@test.com",
            "role": "empresa",
        }
    )

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def override_company_dependencies(
    auth_service_mock,
    certificate_service_mock,
    fake_company_user,
):
    app.dependency_overrides[get_auth_service] = lambda: auth_service_mock
    app.dependency_overrides[get_certificate_service] = lambda: certificate_service_mock
    app.dependency_overrides[get_current_user] = lambda: fake_company_user

    yield

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def company_client(
    override_company_dependencies,
):
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client


# ==========================================
# TESTS - EVENTS
# ==========================================


@pytest.mark.asyncio
async def test_create_event_success(async_client, event_service_mock, auth_headers):

    event_service_mock.create_event.return_value = {
        "_id": "evt_123",
        "name": "Imersão Dev Insights",
        "institution": "Comunidade Frontend Fusion",
        "workload": 9,
        "description": "Evento de tecnologia",
        "start_date": "2025-11-05T00:00:00",
        "end_date": "2025-11-07T00:00:00",
    }

    response = await async_client.post(
        "/api/v1/events",
        json={
            "name": "Imersão Dev Insights",
            "institution": "Comunidade Frontend Fusion",
            "workload": 9,
            "description": "Evento de tecnologia",
            "start_date": "2025-11-05T00:00:00",
            "end_date": "2025-11-07T00:00:00",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201

    body = response.json()

    assert body["success"] is True
    assert body["data"]["event"]["name"] == "Imersão Dev Insights"


@pytest.mark.asyncio
async def test_create_event_invalid_workload(async_client, auth_headers):

    response = await async_client.post(
        "/api/v1/events",
        json={
            "name": "Evento Teste",
            "institution": "Instituição",
            "workload": 0,
            "description": "Descrição",
            "start_date": "2025-11-05T00:00:00",
            "end_date": "2025-11-07T00:00:00",
        },
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_event_end_before_start(async_client, auth_headers):

    response = await async_client.post(
        "/api/v1/events",
        json={
            "name": "Evento Teste",
            "institution": "Instituição",
            "workload": 5,
            "description": "Descrição",
            "start_date": "2025-11-07T00:00:00",
            "end_date": "2025-11-05T00:00:00",
        },
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_event_name_too_short(async_client, auth_headers):

    response = await async_client.post(
        "/api/v1/events",
        json={
            "name": "AB",
            "institution": "Instituição",
            "workload": 5,
            "description": "Descrição",
            "start_date": "2025-11-05T00:00:00",
            "end_date": "2025-11-07T00:00:00",
        },
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_event_without_token(async_client_no_auth):

    response = await async_client_no_auth.post(
        "/api/v1/events",
        json={
            "name": "Evento Teste",
            "institution": "Instituição",
            "workload": 5,
            "description": "Descrição",
            "start_date": "2025-11-05T00:00:00",
            "end_date": "2025-11-07T00:00:00",
        },
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_event_success(async_client, event_service_mock):

    event_service_mock.get_event_by_id.return_value = {
        "_id": "evt_123",
        "name": "Imersão Dev Insights",
        "institution": "Comunidade Frontend Fusion",
        "workload": 9,
    }

    response = await async_client.get("/api/v1/events/evt_123")

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True


@pytest.mark.asyncio
async def test_get_event_not_found(async_client, event_service_mock):

    event_service_mock.get_event_by_id.return_value = None

    response = await async_client.get("/api/v1/events/invalid_id")

    assert response.status_code == 404

# ==========================================
# TESTS - UPDATE EVENT
# ==========================================


@pytest.mark.asyncio
async def test_update_event_success(async_client, event_service_mock, auth_headers):

    event_service_mock.update_event.return_value = {
            "_id": "evt_123",
            "name": "Evento Teste",
            "institution": "Instituição",
            "workload": 5,
            "description": "Descrição",
            "start_date": "2025-11-05T00:00:00",
            "end_date": "2025-11-07T00:00:00",
    }

    response = await async_client.put(
        "/api/v1/events/evt_123",
        json={"name": "Evento Teste Atualizado"},
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Dados atualizados com sucesso"


@pytest.mark.asyncio
async def test_update_event_not_found(async_client, event_service_mock, auth_headers):

    event_service_mock.update_event.side_effect = Exception("Evento não encontrado")

    response = await async_client.put(
        "/api/v1/events/evt_123",
        json={"name": "Evento Teste Atualizado"},
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_event_negative_workload(
    async_client, event_service_mock, auth_headers
):

    event_service_mock.update_event.return_value = {
            "_id": "evt_123",
            "name": "Evento Teste",
            "workload": 5,
    }

    response = await async_client.put(
        "/api/v1/events/evt_123",
        json={
            "name": "Evento Teste Atualizado",
            "workload": 0,
        },
        headers=auth_headers,
    )

    assert response.status_code == 422 # Alerta de Unprocessable Content 

@pytest.mark.asyncio
async def test_update_event_invalid_dates(
    async_client, event_service_mock, auth_headers
):

    event_service_mock.update_event.return_value = {
            "_id": "evt_123",
            "name": "Evento Teste",
            "workload": 5,
            "start_date": "2025-11-05T00:00:00",
            "end_date": "2025-11-06T00:00:00"

    }

    response = await async_client.put(
        "/api/v1/events/evt_123",
        json={
            "name": "Evento Teste Atualizado",
            "start_date": "2025-11-05T00:00:00",
            "end_date": "2025-11-04T00:00:00"
        },
        headers=auth_headers,
    )

    assert response.status_code == 422 # Alerta de Unprocessable Content 

@pytest.mark.asyncio
async def test_update_event_single_date(
    async_client, event_service_mock, auth_headers
):

    event_service_mock.update_event.return_value = {
            "_id": "evt_123",
            "name": "Evento Teste",
            "workload": 5,
            "start_date": "2025-11-05T00:00:00",
            "end_date": "2025-11-06T00:00:00"

    }

    response = await async_client.put(
        "/api/v1/events/evt_123",
        json={
            "name": "Evento Teste Atualizado",
            "end_date": "2025-11-04T00:00:00"
        },
        headers=auth_headers,
    )

    assert response.status_code == 422 # Alerta de Unprocessable Content 



@pytest.mark.asyncio
async def test_create_event_without_token(async_client_no_auth):

    response = await async_client_no_auth.put(
        "/api/v1/events/evt_123",
        json={
            "name": "Evento Teste Atualizado",
        },
    )

    assert response.status_code == 403

# ==========================================
# TESTS - AUTH ENDPOINTS
# ==========================================


@pytest.mark.asyncio
async def test_signup_success(async_client, auth_service_mock):
    from api_certify.models.auth_model import Role

    auth_service_mock.create_auth_user.return_value = {
        "_id": "user123",
        "fullname": "João Silva",
        "email": "joao@example.com",
        "role": Role.USER,
        "status": "pending",
    }

    response = await async_client.post(
        "/api/v1/auth/signup",
        json={
            "fullname": "João Silva",
            "email": "joao@example.com",
            "password": "SenhaSegura123!",
            "role": "user",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Usuário cadastrado com sucesso"


@pytest.mark.asyncio
async def test_signup_error(async_client, auth_service_mock):
    auth_service_mock.create_auth_user.side_effect = Exception("Email já cadastrado")

    response = await async_client.post(
        "/api/v1/auth/signup",
        json={
            "fullname": "João Silva",
            "email": "joao@example.com",
            "password": "SenhaSegura123!",
            "role": "user",
        },
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_error_invalid_credentials(async_client, auth_service_mock):
    auth_service_mock.login_auth.side_effect = Exception("Credenciais inválidas")

    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@email.com",
            "password": "WrongPassword",
        },
    )

    assert response.status_code == 401
    body = response.json()
    assert body["message"] == "Email ou senha incorretos"


@pytest.mark.asyncio
async def test_login_error_email_in_use(async_client, auth_service_mock):
    auth_service_mock.login_auth.side_effect = Exception("Email já cadastrado")

    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@email.com",
            "password": "SenhaSegura123!",
        },
    )

    assert response.status_code == 409
    body = response.json()
    assert "já está em uso" in body["message"]


@pytest.mark.asyncio
async def test_login_error_generic(async_client, auth_service_mock):
    auth_service_mock.login_auth.side_effect = Exception("Erro genérico no login")

    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@email.com",
            "password": "SenhaSegura123!",
        },
    )

    assert response.status_code == 400
    body = response.json()
    assert "Erro no login" in body["message"]


@pytest.mark.asyncio
async def test_get_me_success(async_client, auth_service_mock, auth_headers):
    from api_certify.models.auth_model import Role

    auth_service_mock.get_me.return_value = {
        "_id": "user123",
        "fullname": "Test User",
        "email": "test@email.com",
        "role": Role.USER,
        "status": "available",
    }

    response = await async_client.get(
        "/api/v1/auth/me",
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Usuário autenticado"


@pytest.mark.asyncio
async def test_get_me_error(async_client, auth_service_mock, auth_headers):
    auth_service_mock.get_me.side_effect = Exception("Usuário não encontrado")

    response = await async_client.get(
        "/api/v1/auth/me",
        headers=auth_headers,
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_user_success(async_client, auth_service_mock, auth_headers):
    from api_certify.models.auth_model import Role

    auth_service_mock.update_user.return_value = {
        "_id": "user123",
        "fullname": "Updated Name",
        "email": "test@email.com",
        "role": Role.USER,
        "status": "available",
    }

    response = await async_client.put(
        "/api/v1/auth/user123",
        json={"fullname": "Updated Name"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Dados atualizados com sucesso"


@pytest.mark.asyncio
async def test_update_user_not_found(async_client, auth_service_mock, auth_headers):
    auth_service_mock.update_user.side_effect = Exception("Usuário não encontrado")

    response = await async_client.put(
        "/api/v1/auth/invalid_id",
        json={"fullname": "Updated Name"},
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_user_email_exists(async_client, auth_service_mock, auth_headers):
    auth_service_mock.update_user.side_effect = Exception("Email já cadastrado")

    response = await async_client.put(
        "/api/v1/auth/user123",
        json={"email": "existing@email.com"},
        headers=auth_headers,
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_user_error_generic(async_client, auth_service_mock, auth_headers):
    auth_service_mock.update_user.side_effect = Exception("Erro genérico")

    response = await async_client.put(
        "/api/v1/auth/user123",
        json={"fullname": "Updated Name"},
        headers=auth_headers,
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_refresh_token_success(async_client, auth_service_mock):
    auth_service_mock.refresh_access_token.return_value = {
        "access_token": "new-token",
        "refresh_token": "new-refresh-token",
        "token_type": "bearer",
    }

    response = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "valid-refresh-token"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Token renovado com sucesso"


@pytest.mark.asyncio
async def test_refresh_token_missing(async_client):
    response = await async_client.post(
        "/api/v1/auth/refresh",
        json={},
    )

    assert response.status_code == 400
    body = response.json()
    assert "refresh_token é obrigatório" in body["message"]


@pytest.mark.asyncio
async def test_logout_success(async_client, auth_service_mock, auth_headers):
    auth_service_mock.logout.return_value = {"message": "Logout realizado com sucesso"}

    response = await async_client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": "valid-refresh-token"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Logout realizado com sucesso"


@pytest.mark.asyncio
async def test_logout_missing_token(async_client, auth_headers):
    response = await async_client.post(
        "/api/v1/auth/logout",
        json={},
        headers=auth_headers,
    )

    assert response.status_code == 400
    body = response.json()
    assert "refresh_token é obrigatório" in body["message"]

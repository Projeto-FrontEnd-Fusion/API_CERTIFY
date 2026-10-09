import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from io import BytesIO

from api_certify.main import app
from api_certify.core.security import create_access_token
from api_certify.dependencies import get_current_user


@pytest.fixture
def fake_current_user():
    return {"sub": "user123", "email": "test@email.com", "role": "empresa"}


@pytest.fixture
def auth_headers():
    token = create_access_token(
        {"sub": "user123", "email": "test@email.com", "role": "empresa"}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def override_auth(fake_current_user):
    app.dependency_overrides[get_current_user] = lambda: fake_current_user
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client(override_auth):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_upload_logo_success(async_client, auth_headers):
    file_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    response = await async_client.post(
        "/api/v1/upload/logo",
        files={"file": ("logo.png", BytesIO(file_content), "image/png")},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "/static/uploads/logos/user123.png" in body["data"]["url"]


@pytest.mark.asyncio
async def test_upload_signature_success(async_client, auth_headers):
    file_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    response = await async_client.post(
        "/api/v1/upload/signature",
        files={"file": ("sign.jpg", BytesIO(file_content), "image/jpeg")},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "/static/uploads/signatures/user123.jpg" in body["data"]["url"]


@pytest.mark.asyncio
async def test_upload_invalid_format(async_client, auth_headers):
    file_content = b"fake pdf content"
    response = await async_client.post(
        "/api/v1/upload/logo",
        files={"file": ("doc.pdf", BytesIO(file_content), "application/pdf")},
        headers=auth_headers,
    )

    assert response.status_code == 415


@pytest.mark.asyncio
async def test_upload_file_too_large(async_client, auth_headers):
    # 3MB file
    file_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * (3 * 1024 * 1024)
    response = await async_client.post(
        "/api/v1/upload/logo",
        files={"file": ("big.png", BytesIO(file_content), "image/png")},
        headers=auth_headers,
    )

    assert response.status_code == 413


@pytest.mark.asyncio
async def test_upload_without_token():
    app.dependency_overrides.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        file_content = b"\x89PNG\r\n\x1a\n"
        response = await client.post(
            "/api/v1/upload/logo",
            files={"file": ("logo.png", BytesIO(file_content), "image/png")},
        )

    assert response.status_code == 401

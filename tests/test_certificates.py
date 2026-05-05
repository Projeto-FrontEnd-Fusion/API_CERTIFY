from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from api_certify.models.certificate_model import CertificateInDb, CreateCertificate

# -------------------------
# Fixtures
# -------------------------


@pytest.fixture
def user_id():
    return "user-1"


@pytest.fixture
def certificate_data():
    return CreateCertificate(
        event_id="event-1",
        access_key="key123",
        fullname="Teste User",
        email="teste@example.com",
        status="available",
    )


@pytest.fixture
def certificate_mock(user_id):
    return CertificateInDb(
        _id="cert-1",
        user_id=user_id,
        access_key="key123",
        participant_name="Teste User",
        participant_email="teste@example.com",
        institution_name="Instituto Teste",
        event_id="event-1",
        event_name="Evento Teste",
        description="Certificado de participação",
        workload="10h",
        status="available",
        valid_until=datetime(2030, 1, 1),
    )


# -------------------------
# Create certificate
# -------------------------


@pytest.mark.asyncio
async def test_create_certificate_success(
    certificate_service,
    certificate_repository_mock,
    auth_repository_mock,
    user_id,
    certificate_data,
    certificate_mock,
):
    auth_repository_mock.isExistAuth = AsyncMock(return_value=True)
    certificate_repository_mock.find_existing_certificate = AsyncMock(return_value=None)
    certificate_repository_mock.create = AsyncMock(return_value=certificate_mock)

    result = await certificate_service.create_participant_certificate(
        user_id,
        certificate_data,
    )

    assert result.user_id == user_id
    assert result.event_id == certificate_data.event_id
    assert result.participant_email == certificate_data.email
    assert result.participant_name == certificate_data.fullname


@pytest.mark.asyncio
async def test_create_certificate_existing(
    certificate_service,
    certificate_repository_mock,
    auth_repository_mock,
    user_id,
    certificate_data,
    certificate_mock,
):
    auth_repository_mock.isExistAuth = AsyncMock(return_value=True)
    certificate_repository_mock.find_existing_certificate = AsyncMock(
        return_value=certificate_mock
    )

    result = await certificate_service.create_participant_certificate(
        user_id,
        certificate_data,
    )

    assert result == certificate_mock


@pytest.mark.asyncio
async def test_create_certificate_user_not_exist(
    certificate_service,
    auth_repository_mock,
    user_id,
    certificate_data,
):
    auth_repository_mock.isExistAuth = AsyncMock(return_value=False)

    with pytest.raises(Exception):
        await certificate_service.create_participant_certificate(
            user_id,
            certificate_data,
        )


# -------------------------
# Get many certificates
# -------------------------


@pytest.mark.asyncio
async def test_get_many_certificates_success(
    certificate_service,
    certificate_repository_mock,
    user_id,
    certificate_mock,
):
    certificate_repository_mock.get_many_certificates = AsyncMock(
        return_value=[certificate_mock]
    )

    result = await certificate_service.get_many_certificates(user_id)

    assert len(result) == 1
    assert result[0].user_id == user_id


@pytest.mark.asyncio
async def test_get_many_certificates_empty(
    certificate_service,
    certificate_repository_mock,
    user_id,
):
    certificate_repository_mock.get_many_certificates = AsyncMock(return_value=[])

    result = await certificate_service.get_many_certificates(user_id)

    assert result == []


@pytest.mark.asyncio
async def test_get_many_certificates_with_pagination(
    certificate_service,
    certificate_repository_mock,
    user_id,
    certificate_mock,
):
    certificate_repository_mock.get_many_certificates = AsyncMock(
        return_value=[certificate_mock]
    )

    result = await certificate_service.get_many_certificates(
        user_id,
        skip=5,
        limit=10,
    )

    certificate_repository_mock.get_many_certificates.assert_awaited_once_with(
        user_id=user_id,
        skip=5,
        limit=10,
    )

    assert len(result) == 1
    assert result[0].user_id == user_id


@pytest.mark.asyncio
async def test_get_many_certificates_limit_capped_at_100(
    certificate_service,
    certificate_repository_mock,
    user_id,
):
    certificate_repository_mock.get_many_certificates = AsyncMock(return_value=[])

    await certificate_service.get_many_certificates(
        user_id,
        skip=0,
        limit=150,
    )

    certificate_repository_mock.get_many_certificates.assert_awaited_once_with(
        user_id=user_id,
        skip=0,
        limit=100,
    )


# -------------------------
# Get certificate by ID
# -------------------------


@pytest.mark.asyncio
async def test_get_certificate_by_id_success(
    certificate_service,
    certificate_repository_mock,
    certificate_mock,
):
    certificate_repository_mock.get_certificate = AsyncMock(
        return_value=certificate_mock
    )

    result = await certificate_service.get_certificate_by_id("cert-1")

    assert result.id == "cert-1"
    assert result.event_id == "event-1"


@pytest.mark.asyncio
async def test_get_certificate_by_id_not_found(
    certificate_service,
    certificate_repository_mock,
):
    certificate_repository_mock.get_certificate = AsyncMock(
        side_effect=Exception("Certificado não encontrado.")
    )

    with pytest.raises(Exception, match="Certificado não encontrado"):
        await certificate_service.get_certificate_by_id("invalid-id")


# -------------------------
# Validate certificate
# -------------------------


@pytest.mark.asyncio
async def test_validate_certificate_success(
    certificate_service,
    certificate_repository_mock,
):
    certificate_repository_mock.find_by_access_key = AsyncMock(
        return_value={
            "participant_name": "Teste User",
            "event_name": "Evento Teste",
            "workload": "10h",
            "issued_at": "2025-01-01T00:00:00",
            "event_start": "2025-01-01T00:00:00",
            "event_end": "2025-01-03T00:00:00",
        }
    )

    result = await certificate_service.validate_certificate("key123")

    assert result.participant_name == "Teste User"
    assert result.event_name == "Evento Teste"


@pytest.mark.asyncio
async def test_validate_certificate_not_found(
    certificate_service,
    certificate_repository_mock,
):
    certificate_repository_mock.find_by_access_key = AsyncMock(return_value=None)

    with pytest.raises(Exception, match="Certificado não encontrado"):
        await certificate_service.validate_certificate("invalid-key")

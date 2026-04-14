import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from api_certify.models.certificate_model import CreateCertificate, CertificateInDb


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
# Tests
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

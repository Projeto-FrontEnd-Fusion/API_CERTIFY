import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from api_certify.models.certificate_model import (
    CreateCertificate,
    CertificateInDb,
)


def certificate_mock(user_id: str):
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


@pytest.mark.asyncio
async def test_create_certificate_success(
    certificate_service,
    certificate_repository_mock,
    auth_repository_mock,
):

    user_id = "user-1"

    cert_data = CreateCertificate(
        event_id="event-1",
        access_key="key123",
        fullname="Teste User",
        email="teste@example.com",
        status="available",
    )

    auth_repository_mock.isExistAuth = AsyncMock(return_value=True)

    certificate_repository_mock.find_existing_certificate = AsyncMock(return_value=None)

    certificate_repository_mock.create = AsyncMock(
        return_value=certificate_mock(user_id)
    )

    result = await certificate_service.create_participant_certificate(
        user_id,
        cert_data,
    )

    assert result.user_id == user_id
    assert result.event_id == cert_data.event_id


@pytest.mark.asyncio
async def test_create_certificate_existing(
    certificate_service,
    certificate_repository_mock,
    auth_repository_mock,
):

    user_id = "user-1"

    cert_data = CreateCertificate(
        event_id="event-1",
        access_key="key123",
        fullname="Teste User",
        email="teste@example.com",
        status="available",
    )

    auth_repository_mock.isExistAuth = AsyncMock(return_value=True)

    existing_certificate = certificate_mock(user_id)

    certificate_repository_mock.find_existing_certificate = AsyncMock(
        return_value=existing_certificate
    )

    result = await certificate_service.create_participant_certificate(
        user_id,
        cert_data,
    )

    assert result == existing_certificate


@pytest.mark.asyncio
async def test_create_certificate_user_not_exist(
    certificate_service,
    auth_repository_mock,
):

    user_id = "user-404"

    cert_data = CreateCertificate(
        event_id="event-1",
        access_key="key123",
        fullname="Teste User",
        email="teste@example.com",
        status="available",
    )

    auth_repository_mock.isExistAuth = AsyncMock(return_value=False)

    with pytest.raises(Exception):
        await certificate_service.create_participant_certificate(
            user_id,
            cert_data,
        )

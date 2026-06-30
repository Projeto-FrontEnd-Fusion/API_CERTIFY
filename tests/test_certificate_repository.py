import pytest
from datetime import datetime, timezone
from mongomock_motor import AsyncMongoMockClient

import os

from api_certify.models.certificate_model import CertificateInDb, CreateCertificate
from api_certify.repositories.certificate_repository import CertificateRepository


@pytest.mark.asyncio
async def test_get_certificates_by_issuer_filters_and_pagination():
    client = AsyncMongoMockClient()
    db = client["CERTIFY"]

    now = datetime.now(timezone.utc)

    certificates = [
        {
            "user_id": "user1",
            "issuer_id": "company123",
            "institution_name": "Company 123",
            "event_id": "event-1",
            "access_key": "KEY123",
            "status": "available",
            "participant_name": "João Silva",
            "participant_email": "joao@example.com",
            "event_name": "Evento 1",
            "description": "Descrição",
            "workload": "8h",
            "event_start": now,
            "event_end": now,
            "event_date": now,
            "issued_at": now,
            "valid_until": now,
        },
        {
            "user_id": "user2",
            "issuer_id": "company123",
            "institution_name": "Company 123",
            "event_id": "event-2",
            "access_key": "KEY124",
            "status": "pending",
            "participant_name": "Maria Souza",
            "participant_email": "maria@example.com",
            "event_name": "Evento 2",
            "description": "Descrição",
            "workload": "4h",
            "event_start": now,
            "event_end": now,
            "event_date": now,
            "issued_at": now,
            "valid_until": now,
        },
        {
            "user_id": "user3",
            "issuer_id": "other-company",
            "institution_name": "Outra Empresa",
            "event_id": "event-1",
            "access_key": "KEY125",
            "status": "available",
            "participant_name": "Carlos Lima",
            "participant_email": "carlos@example.com",
            "event_name": "Evento 1",
            "description": "Descrição",
            "workload": "8h",
            "event_start": now,
            "event_end": now,
            "event_date": now,
            "issued_at": now,
            "valid_until": now,
        },
    ]

    await db.certificates.insert_many(certificates)

    repo = CertificateRepository(db)

    result = await repo.get_certificates_by_issuer(
        empresa_id="company123",
        skip=0,
        limit=10,
        page=1,
        event_id="event-1",
        status="available",
    )

    assert result["total"] == 1
    assert result["page"] == 1
    assert result["limit"] == 10
    assert result["total_pages"] == 1
    assert len(result["items"]) == 1
    assert isinstance(result["items"][0], CertificateInDb)
    assert result["items"][0].issuer_id == "company123"
    assert result["items"][0].status == "available"
    assert result["items"][0].event_id == "event-1"


@pytest.mark.asyncio
async def test_create_certificate_stores_issuer_id():
    client = AsyncMongoMockClient()
    db = client["CERTIFY"]

    repo = CertificateRepository(db)

    payload = CreateCertificate(
        fullname="João Silva",
        access_key=os.getenv("ACCESS_KEY", "ACCESS_KEY_NOT_SET"),
        event_id="event-1",
        status="pending",
        email="joao@example.com",
    )

    created = await repo.create("user1", payload, issuer_id="company123")

    assert created.issuer_id == "company123"

    inserted = await db.certificates.find_one({"issuer_id": "company123"})
    assert inserted is not None
    assert inserted["issuer_id"] == "company123"

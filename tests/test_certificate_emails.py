import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from bson import ObjectId
from mongomock_motor import AsyncMongoMockClient

from api_certify.models.certificate_model import (
    BatchCertificateRequest,
    CreateCertificate,
)
from api_certify.repositories.auth_repository import AuthRepository
from api_certify.repositories.certificate_repository import (
    ACCESS_KEY,
    CertificateRepository,
)
from api_certify.service.certificate_email_service import (
    CertificateEmailService,
    SMTPTransport,
)
from api_certify.service.certificate_service import CertificateService


class FakeSMTP:
    host = 'smtp.test'
    sender = 'certify@example.com'

    def __init__(self):
        self.messages = []
        self.fail_student = False

    def send(self, message):
        if self.fail_student and message['To'] == 'student@example.com':
            raise ConnectionError('unavailable')
        self.messages.append(message)


async def setup_services():
    database = AsyncMongoMockClient().certificate_email_test
    company_id, student_id = ObjectId(), ObjectId()
    await database.auth_database.insert_many(
        [
            {
                '_id': company_id,
                'fullname': 'Empresa Teste',
                'email': 'company@example.com',
                'role': 'empresa',
                'password': 'hashed',
            },
            {
                '_id': student_id,
                'fullname': 'Aluno Teste',
                'email': 'student@example.com',
                'role': 'user',
                'password': 'hashed',
            },
        ]
    )
    auth = AuthRepository(database)
    repository = CertificateRepository(database)
    transport = FakeSMTP()
    email = CertificateEmailService(
        repository.certificate_collection,
        auth,
        transport,
        'https://certify.example',
    )
    events = AsyncMock()
    events.exists.return_value = True
    events.find_by_id.return_value = {
        '_id': 'event-1',
        'name': 'Curso <script> & testes',
        'institution': 'Empresa Teste',
        'description': 'Participacao',
        'workload': 20,
    }
    service = CertificateService(repository, auth, events, email_service=email)
    return database, service, transport, str(company_id), str(student_id)


@pytest.mark.asyncio
async def test_emission_queues_and_delivers_to_student_and_issuer_without_duplicates():
    (
        database,
        service,
        transport,
        company_id,
        student_id,
    ) = await setup_services()
    payload = CreateCertificate(
        fullname='Aluno Teste',
        email='student@example.com',
        event_id='event-1',
        access_key=ACCESS_KEY,
        status='available',
    )
    certificate = await service.create_participant_certificate(
        student_id, payload, issuer_id=company_id
    )
    stored = await database.certificates.find_one(
        {'_id': ObjectId(certificate.id)}
    )
    assert stored['issuer_id'] == company_id
    assert stored['notifications']['student']['status'] == 'pending'
    await service.send_pending_notifications()
    assert {str(message['To']) for message in transport.messages} == {
        'student@example.com',
        'company@example.com',
    }
    student_message = next(
        m for m in transport.messages if m['To'] == 'student@example.com'
    )
    assert (
        f'https://certify.example/validar-certificado/{certificate.access_key}'
        in student_message.get_body(preferencelist=('plain',)).get_content()
    )
    html = student_message.get_body(preferencelist=('html',)).get_content()
    assert '<script>' not in html
    assert '&lt;script&gt;' in html
    assert student_message.get_content_type() == 'multipart/alternative'
    duplicate = await service.create_participant_certificate(
        student_id, payload, issuer_id=company_id
    )
    assert duplicate.id == certificate.id
    await service.send_pending_notifications()
    assert len(transport.messages) == 2


@pytest.mark.asyncio
async def test_batch_notifies_registered_and_guest_students_and_persists_issuer():
    database, service, transport, company_id, _ = await setup_services()
    payload = BatchCertificateRequest(
        event_id='event-1',
        participants=[
            {'fullname': 'Aluno Teste', 'email': 'student@example.com'},
            {'fullname': 'Aluno Convidado', 'email': 'guest@example.com'},
        ],
    )
    summary = await service.create_batch_certificates(
        payload, issuer_id=company_id
    )
    assert summary.criados == 2
    await service.send_pending_notifications()
    assert len(transport.messages) == 4
    assert (
        sum(m['To'] == 'company@example.com' for m in transport.messages) == 2
    )
    assert sum(m['To'] == 'guest@example.com' for m in transport.messages) == 1
    assert (
        await database.certificates.count_documents({'issuer_id': company_id})
        == 2
    )
    duplicate_summary = await service.create_batch_certificates(
        payload, issuer_id=company_id
    )
    assert duplicate_summary.duplicados_ignorados == 2
    await service.send_pending_notifications()
    assert len(transport.messages) == 4


@pytest.mark.asyncio
async def test_failed_recipient_retries_without_resending_company_mail():
    (
        database,
        service,
        transport,
        company_id,
        student_id,
    ) = await setup_services()
    payload = CreateCertificate(
        fullname='Aluno Teste',
        email='student@example.com',
        event_id='event-1',
        access_key=ACCESS_KEY,
        status='available',
    )
    await service.create_participant_certificate(
        student_id, payload, issuer_id=company_id
    )
    transport.fail_student = True
    await service.send_pending_notifications()
    stored = await database.certificates.find_one({})
    assert stored['notifications']['student']['status'] == 'failed'
    assert stored['notifications']['company']['status'] == 'sent'
    assert stored['notifications']['student']['error'] == 'ConnectionError'
    await service.send_pending_notifications()
    assert len(transport.messages) == 1
    transport.fail_student = False
    await database.certificates.update_one(
        {},
        {
            '$set': {
                'notifications.student.retry_at': datetime.now(timezone.utc)
                - timedelta(seconds=1)
            }
        },
    )
    await asyncio.gather(
        service.send_pending_notifications(),
        service.send_pending_notifications(),
    )
    assert len(transport.messages) == 2
    stored = await database.certificates.find_one({})
    assert stored['notifications']['student']['status'] == 'sent'


@pytest.mark.asyncio
async def test_missing_configuration_keeps_notifications_pending():
    (
        database,
        service,
        transport,
        company_id,
        student_id,
    ) = await setup_services()
    payload = CreateCertificate(
        fullname='Aluno Teste',
        email='student@example.com',
        event_id='event-1',
        access_key=ACCESS_KEY,
        status='available',
    )
    await service.create_participant_certificate(
        student_id, payload, issuer_id=company_id
    )
    transport.host = ''
    await service.send_pending_notifications()
    assert transport.messages == []
    stored = await database.certificates.find_one({})
    assert stored['notifications']['student']['status'] == 'pending'


def test_smtp_uses_tls_authentication_and_message(monkeypatch):
    for key, value in {
        'SMTP_HOST': 'smtp.test',
        'SMTP_FROM': 'certify@example.com',
        'SMTP_USERNAME': 'login',
        'SMTP_PASSWORD': 'test-password',
        'SMTP_SECURITY': 'starttls',
    }.items():
        monkeypatch.setenv(key, value)
    with patch(
        'api_certify.service.certificate_email_service.smtplib.SMTP'
    ) as smtp:
        smtp.return_value.__enter__.return_value.send_message.return_value = {}
        transport = SMTPTransport()
        from email.message import EmailMessage

        message = EmailMessage()
        transport.send(message)
        connection = smtp.return_value.__enter__.return_value
        connection.starttls.assert_called_once()
        connection.login.assert_called_once_with('login', 'test-password')
        connection.send_message.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_worker_resumes_interrupted_send_after_restart():
    database, service, transport, company_id, student_id = await setup_services()
    payload = CreateCertificate(
        fullname='Aluno Teste', email='student@example.com', event_id='event-1',
        access_key=ACCESS_KEY, status='available',
    )
    await service.create_participant_certificate(student_id, payload, issuer_id=company_id)
    await database.certificates.update_one({}, {'$set': {
        'notifications.student.status': 'sending',
        'notifications.student.claimed_at': datetime.now(timezone.utc) - timedelta(minutes=6),
        'notifications.company.status': 'sent',
    }})
    restarted = CertificateEmailService(database.certificates, AuthRepository(database), transport, 'https://certify.example')
    await restarted.dispatch_pending()
    assert len(transport.messages) == 1
    assert transport.messages[0]['To'] == 'student@example.com'
    assert (await database.certificates.find_one({}))['notifications']['student']['status'] == 'sent'


@pytest.mark.asyncio
async def test_deferred_links_send_only_selected_students_and_do_not_duplicate():
    database, service, transport, company_id, _ = await setup_services()
    summary = await service.create_batch_certificates(BatchCertificateRequest(
        event_id='event-1', notify_students=False, participants=[
            {'fullname': 'Aluno Teste', 'email': 'student@example.com'},
            {'fullname': 'Outro Aluno', 'email': 'other@example.com'},
        ],
    ), issuer_id=company_id)
    assert summary.criados == 2
    await service.send_pending_notifications()
    assert all(message['To'] == 'company@example.com' for message in transport.messages)
    documents = await database.certificates.find({}).to_list(10)
    student = next(doc for doc in documents if doc['participant_email'] == 'student@example.com')
    other = next(doc for doc in documents if doc['participant_email'] == 'other@example.com')
    ids = [str(student['_id']), str(student['_id'])]
    result = await service.send_links(ids, {'sub': company_id, 'role': 'empresa'})
    assert result == {'total': 1, 'sent': 1, 'failed': 0, 'pending': 0}
    await service.send_links(ids, {'sub': company_id, 'role': 'empresa'})
    assert sum(message['To'] == 'student@example.com' for message in transport.messages) == 1
    assert (await database.certificates.find_one({'_id': other['_id']}))['notifications']['student']['status'] == 'deferred'


@pytest.mark.asyncio
async def test_send_links_checks_ownership_before_changing_any_notification():
    from fastapi import HTTPException

    database, service, transport, company_id, _ = await setup_services()
    await service.create_batch_certificates(BatchCertificateRequest(
        event_id='event-1', notify_students=False,
        participants=[{'fullname': 'Aluno Teste', 'email': 'student@example.com'}],
    ), issuer_id=company_id)
    doc = await database.certificates.find_one({})
    with pytest.raises(HTTPException) as error:
        await service.send_links([str(doc['_id'])], {'sub': 'another-company', 'role': 'empresa'})
    assert error.value.status_code == 403
    assert transport.messages == []
    assert (await database.certificates.find_one({}))['notifications']['student']['status'] == 'deferred'


@pytest.mark.asyncio
async def test_send_links_reports_smtp_failure_and_missing_configuration():
    from fastapi import HTTPException

    database, service, transport, company_id, _ = await setup_services()
    await service.create_batch_certificates(BatchCertificateRequest(
        event_id='event-1', notify_students=False,
        participants=[{'fullname': 'Aluno Teste', 'email': 'student@example.com'}],
    ), issuer_id=company_id)
    doc = await database.certificates.find_one({})
    transport.host = ''
    with pytest.raises(HTTPException) as error:
        await service.send_links([str(doc['_id'])], {'sub': company_id, 'role': 'empresa'})
    assert error.value.status_code == 503
    assert (await database.certificates.find_one({}))['notifications']['student']['status'] == 'deferred'
    transport.host = 'smtp.test'
    transport.fail_student = True
    result = await service.send_links([str(doc['_id'])], {'sub': company_id, 'role': 'empresa'})
    assert result == {'total': 1, 'sent': 0, 'failed': 1, 'pending': 0}


@pytest.mark.asyncio
async def test_public_validation_uses_actual_data_and_rejects_expired_certificate():
    from fastapi import HTTPException

    database, service, _, company_id, student_id = await setup_services()
    certificate = await service.create_participant_certificate(student_id, CreateCertificate(
        fullname='Aluno Teste', email='student@example.com', event_id='event-1',
        access_key=ACCESS_KEY, status='available',
    ), issuer_id=company_id)
    result = await service.validate_certificate(certificate.access_key)
    assert result.institution_name == 'Empresa Teste'
    assert result.access_key == certificate.access_key
    assert 'participant_email' not in result.model_dump()
    assert 'notifications' not in result.model_dump()
    await database.certificates.update_one({}, {'$set': {'valid_until': datetime.now(timezone.utc) - timedelta(days=1)}})
    with pytest.raises(HTTPException) as error:
        await service.validate_certificate(certificate.access_key)
    assert error.value.status_code == 404

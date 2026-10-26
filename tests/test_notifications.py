from datetime import datetime, timedelta, timezone

import pytest
from bson import ObjectId
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

from api_certify.dependencies import get_current_user
from api_certify.main import app
from api_certify.routes.v1.notification_routes import get_notification_service
from api_certify.service.notification_service import NotificationService


@pytest.fixture
def database():
    return AsyncMongoMockClient().notifications_test


async def issue(database, owner='company', **extra):
    data = {
        'issuer_id': owner,
        'participant_name': 'Aluno Real',
        'event_name': 'Curso Real',
        'issued_at': datetime.now(timezone.utc),
        **extra,
    }
    return (await database.certificates.insert_one(data)).inserted_id


@pytest.mark.asyncio
async def test_feed_uses_existing_certificates_and_persists_read_state(
    database,
):
    certificate_id = await issue(database)
    await issue(database, owner='other')
    service = NotificationService(database)
    page = await service.list('company')
    assert page['total'] == page['unread_count'] == 1
    event = page['items'][0]
    assert event['id'] == f'{certificate_id}:issued'
    assert event['description'] == 'Aluno Real — Curso Real'
    assert event['href'] == f'/certificados/visualizar/{certificate_id}'
    await service.mark_read('company', event['id'])
    await service.mark_read('company', event['id'])
    reloaded = await NotificationService(database).list('company')
    assert reloaded['items'][0]['read'] is True
    assert reloaded['unread_count'] == 0
    assert await database.notification_reads.count_documents({}) == 1


@pytest.mark.asyncio
async def test_send_events_use_real_status_and_failed_attempt_is_prioritized(
    database,
):
    now = datetime.now(timezone.utc)
    sent = await issue(
        database,
        notifications={
            'student': {
                'status': 'sent',
                'sent_at': now,
                'attempts': 1,
            }
        },
    )
    failed = await issue(
        database,
        notifications={
            'student': {
                'status': 'failed',
                'claimed_at': now - timedelta(days=1),
                'attempts': 2,
                'error': 'SECRET MUST NOT LEAK',
            }
        },
    )
    await issue(database, notifications={'student': {'status': 'deferred'}})
    service = NotificationService(database)
    page = await service.list('company', limit=2)
    assert page['total'] == page['unread_count'] == 5
    assert page['total_pages'] == 3
    assert page['items'][0]['id'] == f'{failed}:failed:2'
    assert 'SECRET' not in str(page)
    second = await service.list('company', page=2, limit=2)
    assert len(second['items']) == 2
    all_items = (await service.list('company', limit=100))['items']
    assert any(item['id'] == f'{sent}:sent' for item in all_items)


@pytest.mark.asyncio
async def test_read_all_is_scoped_idempotent_and_does_not_hide_new_events(
    database,
):
    for _ in range(7):
        await issue(database)
    other = await issue(database, owner='other')
    service = NotificationService(database)
    assert await service.mark_all_read('company') == 7
    assert await service.mark_all_read('company') == 0
    assert (await service.list('company'))['unread_count'] == 0
    assert (await service.list('other'))['unread_count'] == 1
    await issue(database)
    assert (await service.list('company'))['unread_count'] == 1
    for event_id in (f'{other}:issued', f'{ObjectId()}:issued'):
        with pytest.raises(HTTPException) as error:
            await service.mark_read('company', event_id)
        assert error.value.status_code == 404


@pytest.mark.asyncio
async def test_http_contract_and_permissions(database):
    certificate_id = await issue(database)
    user = {'sub': 'company', 'role': 'empresa'}
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_notification_service] = lambda: (
        NotificationService(database)
    )
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url='http://test'
        ) as client:
            response = await client.get('/api/v1/notifications')
            assert response.status_code == 200
            event = response.json()['data']['items'][0]
            assert event['created_at'].endswith('Z')
            response = await client.patch(
                f'/api/v1/notifications/{certificate_id}:issued/read'
            )
            assert response.json()['data']['notification']['read'] is True
            assert (
                await client.patch('/api/v1/notifications/read-all')
            ).json()['data']['updated'] == 0
            assert (
                await client.get('/api/v1/notifications?limit=101')
            ).status_code == 422
            assert (
                await client.get('/api/v1/notifications?page=0')
            ).status_code == 422
            user['role'] = 'user'
            assert (
                await client.get('/api/v1/notifications')
            ).status_code == 403
            assert (
                await client.patch('/api/v1/notifications/read-all')
            ).status_code == 403
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_empty_feed_has_no_mock_data(database):
    service = NotificationService(database)
    assert await service.list('company') == {
        'items': [],
        'total': 0,
        'unread_count': 0,
        'page': 1,
        'total_pages': 0,
    }
    assert await service.mark_all_read('company') == 0


@pytest.mark.asyncio
async def test_http_requires_real_jwt_and_hides_other_company(database):
    from api_certify.core.security import create_access_token

    certificate_id = await issue(database, owner='other')
    app.dependency_overrides[get_notification_service] = lambda: (
        NotificationService(database)
    )
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url='http://test'
        ) as client:
            assert (await client.get('/api/v1/notifications')).status_code in {
                401,
                403,
            }
            client.headers['Authorization'] = 'Bearer invalid'
            assert (
                await client.get('/api/v1/notifications')
            ).status_code == 401
            token = create_access_token(
                {
                    'sub': 'company',
                    'email': 'company@example.com',
                    'role': 'empresa',
                }
            )
            client.headers['Authorization'] = f'Bearer {token}'
            response = await client.get('/api/v1/notifications')
            assert response.json()['data']['total'] == 0
            assert (
                await client.patch(
                    f'/api/v1/notifications/{certificate_id}:issued/read'
                )
            ).status_code == 404
            assert await database.notification_reads.count_documents({}) == 0
    finally:
        app.dependency_overrides.clear()

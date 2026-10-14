from datetime import datetime, timezone
from http import HTTPStatus
import pytest
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient
from api_certify.dependencies import get_current_user
from api_certify.main import app
from api_certify.routes.v1.dashboard_routes import get_dashboard_service
from api_certify.service.dashboard_service import DashboardService


@pytest.mark.asyncio
async def test_real_counts_scope_and_months():
    db = AsyncMongoMockClient().dashboard_test
    now = datetime(2026, 2, 15, tzinfo=timezone.utc)
    for owner, email, status, issued in [
        ('company', 'ALUNO@example.com', 'sent', now),
        ('company', ' aluno@example.com ', 'failed', now),
        (
            'company',
            'second@example.com',
            'deferred',
            datetime(2025, 12, 1, tzinfo=timezone.utc),
        ),
        ('other', 'third@example.com', 'pending', now),
        ('company', 'draft@example.com', 'pending', None),
    ]:
        await db.certificates.insert_one(
            {
                'issuer_id': owner,
                'participant_email': email,
                'participant_name': 'Aluno Real',
                'event_name': 'Curso Real',
                'issued_at': issued,
                'notifications': {'student': {'status': status}},
            }
        )
    data = await DashboardService(db).summary('company', now)
    assert (
        data['issued'],
        data['sent'],
        data['pending_delivery'],
        data['participants'],
    ) == (3, 1, 2, 2)
    assert data['emissions'] == [
        {'month': month, 'emissions': count}
        for month, count in [
            ('2025-09', 0),
            ('2025-10', 0),
            ('2025-11', 0),
            ('2025-12', 1),
            ('2026-01', 0),
            ('2026-02', 2),
        ]
    ]
    assert len(data['recent_activities']) == data['issued']
    empty = await DashboardService(db).summary('empty', now)
    assert (
        empty['issued']
        == empty['participants']
        == empty['pending_delivery']
        == empty['sent']
        == 0
    )
    assert empty['recent_activities'] == []


@pytest.mark.asyncio
async def test_http_auth_contract():
    db = AsyncMongoMockClient().dashboard_http
    await db.certificates.insert_one(
        {'issuer_id': 'other', 'issued_at': datetime.now(timezone.utc)}
    )
    user = {'sub': 'company', 'role': 'empresa'}
    app.dependency_overrides[get_dashboard_service] = lambda: DashboardService(
        db
    )
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url='http://test'
        ) as client:
            assert (
                await client.get('/api/v1/dashboard')
            ).status_code == HTTPStatus.UNAUTHORIZED
            app.dependency_overrides[get_current_user] = lambda: user
            response = await client.get('/api/v1/dashboard?owner=other')
            assert response.status_code == HTTPStatus.OK
            assert response.json()['data']['issued'] == 0
            assert response.json()['success'] is True
            user['role'] = 'user'
            assert (
                await client.get('/api/v1/dashboard')
            ).status_code == HTTPStatus.FORBIDDEN
    finally:
        app.dependency_overrides.clear()

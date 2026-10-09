from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from api_certify.main import app


@pytest.mark.asyncio
async def test_readiness_requires_a_working_database(monkeypatch):
    database = AsyncMock()
    connection = AsyncMock(return_value=database)
    monkeypatch.setattr('api_certify.main.db_mongo.get_database', connection)
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        response = await client.get('/ready')
        assert response.status_code == 200
        database.command.assert_awaited_once_with('ping')
        database.command.side_effect = RuntimeError('database unavailable')
        response = await client.get('/ready')
        assert response.status_code == 503
        assert response.json() == {'status': 'not_ready'}


@pytest.mark.asyncio
async def test_cors_allows_status_updates_from_frontend():
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        response = await client.options('/api/v1/certificate/test/status', headers={
            'Origin': 'http://localhost:5173',
            'Access-Control-Request-Method': 'PATCH',
            'Access-Control-Request-Headers': 'authorization',
        })
        assert response.status_code == 200
        assert response.headers['access-control-allow-origin'] == 'http://localhost:5173'

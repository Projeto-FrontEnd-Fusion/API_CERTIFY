from io import BytesIO
from unittest.mock import AsyncMock

import pytest
from bson import ObjectId
from fastapi import FastAPI, UploadFile
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient
from starlette.datastructures import Headers

from api_certify.core.security import HashManager
from api_certify.dependencies import get_auth_service, get_current_user
from api_certify.repositories.auth_repository import AuthRepository
from api_certify.routes.v1.auth_routes import auth_routes
from api_certify.routes.v1.upload_routes import upload_routes
from api_certify.service.auth_service import AuthService
from api_certify.service.upload_service import UploadService


@pytest.mark.asyncio
async def test_profile_avatar_and_password_persist(tmp_path, monkeypatch):
    monkeypatch.setattr('api_certify.service.upload_service.UPLOAD_DIR', tmp_path)
    database = AsyncMongoMockClient().profile_test
    repository = AuthRepository(database)
    user_id = ObjectId()
    await database.auth_database.insert_one({
        '_id': user_id, 'fullname': 'Aluno Teste', 'email': 'aluno@example.com',
        'role': 'user', 'password': HashManager.hash_password('OldPass123!'),
    })
    service = AuthService(repository, AsyncMock())
    app = FastAPI()
    app.include_router(auth_routes, prefix='/api/v1')
    app.include_router(upload_routes, prefix='/api/v1')
    app.dependency_overrides[get_current_user] = lambda: {'sub': str(user_id), 'role': 'user'}
    app.dependency_overrides[get_auth_service] = lambda: service
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        response = await client.put(f'/api/v1/auth/{user_id}', json={
            'fullname': 'Aluno Atualizado', 'phone': '43999999999',
            'cpf': '12345678909', 'birth_date': '01/10/1996',
        })
        assert response.status_code == 200
        assert response.json()['data']['auth']['phone'] == '43999999999'
        forbidden = await client.put(f'/api/v1/auth/{ObjectId()}', json={'fullname': 'Outro Aluno'})
        assert forbidden.status_code == 403
        image = b'\x89PNG\r\n\x1a\n' + b'test-image'
        uploaded = await client.post('/api/v1/upload/avatar', files={'file': ('photo.png', image, 'image/png')})
        assert uploaded.status_code == 200
        url = uploaded.json()['data']['url']
        assert (tmp_path / 'avatars' / url.rsplit('/', 1)[1]).read_bytes() == image
        profile = (await client.get('/api/v1/auth/me')).json()['data']['auth']
        assert profile['avatar_url'] == url
        assert profile['birth_date'] == '01/10/1996'
        assert 'password' not in profile
        bad = await client.post('/api/v1/auth/change-password', json={'current_password': 'wrong', 'new_password': 'NewPass123!'})
        assert bad.status_code == 400
        changed = await client.post('/api/v1/auth/change-password', json={'current_password': 'OldPass123!', 'new_password': 'NewPass123!'})
        assert changed.status_code == 200
        stored = await database.auth_database.find_one({'_id': user_id})
        assert HashManager.verify_password('NewPass123!', stored['password'])


@pytest.mark.asyncio
@pytest.mark.parametrize('name,content,mime,expected', [
    ('avatar.svg', b'<svg/>', 'image/svg+xml', 415),
    ('avatar.jpg', b'not an image', 'image/jpeg', 415),
    ('avatar.png', b'\x89PNG\r\n\x1a\n' + b'x' * (5 * 1024 * 1024), 'image/png', 413),
], ids=['svg', 'invalid-image', 'oversized'])
async def test_avatar_rejects_invalid_uploads(tmp_path, monkeypatch, name, content, mime, expected):
    monkeypatch.setattr('api_certify.service.upload_service.UPLOAD_DIR', tmp_path)
    file = UploadFile(filename=name, file=BytesIO(content), headers=Headers({'content-type': mime}))
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as error:
        await UploadService().upload_avatar('user123', file)
    assert error.value.status_code == expected
    assert not list(tmp_path.iterdir())

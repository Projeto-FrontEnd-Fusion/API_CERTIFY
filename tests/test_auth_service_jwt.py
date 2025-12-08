import pytest
from unittest.mock import AsyncMock

from api_certify.service.auth_service import AuthService
from api_certify.models.auth_model import AuthUserLogin, AuthUserReponse
from api_certify.models.jwt_model import Token, TokenData, TokenResponse


@pytest.mark.asyncio
async def test_generate_token():
    fake_user = AuthUserReponse(
        _id="1",
        fullname="Douglas Phelipe",
        email="douglas@gmail.com",
        role="user",
        status="active",
        created_at=None,
        updated_at=None
    )
    
    mock_jwt_manager = AsyncMock()
    mock_jwt_manager.create_jwt.return_value = Token(
        access_token="fake_token",
        expires_in="1800"  # string, se o modelo Token exige string
    )
    
    service = AuthService(auth_repository=None, jwt_manager=mock_jwt_manager)
    
    token = await service.generate_token(fake_user)
    
    
    mock_jwt_manager.create_jwt.assert_awaited_once_with(
        TokenData(
        sub=fake_user.id,
        role=fake_user.role
        )
    )

    assert token.access_token == "fake_token"


@pytest.mark.asyncio
async def test_login_auth():
    mock_repo = AsyncMock()
    fake_user = AuthUserReponse(_id="1", fullname="Douglas Phelipe", email="douglas@example.com", role="admin")
    mock_repo.login.return_value = fake_user
    
    mock_jwt_manager = AsyncMock()
    mock_jwt_manager.create_jwt.return_value = Token(
    access_token="fake_token",
    expires_in="1800"
    )
    
    service = AuthService(auth_repository=mock_repo, jwt_manager=mock_jwt_manager)
    
    login_data = AuthUserLogin(email="test@example.com", password="testando012@")
    
    response = await service.login_auth(login_data)
        
    mock_repo.login.assert_awaited_once_with(login_data)
    mock_jwt_manager.create_jwt.assert_awaited_once()
    assert response["user"] == fake_user
    assert response["access_token"] == "fake_token"
    assert response["token_type"] == "bearer"
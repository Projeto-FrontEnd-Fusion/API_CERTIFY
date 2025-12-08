from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
import pytest
from api_certify.core.security.jwt_manager import JWTManager
from api_certify.dependencies import get_current_active_user, get_current_user, require_roles
from api_certify.models.jwt_model import TokenData


def test_get_current_user():
    fake_token = "fake.jwt.token"
    fake_payload = TokenData(sub="123", role="user")
    
    with patch.object(JWTManager, "verify_and_decode_jwt", return_value=fake_payload):
        result = get_current_user(fake_token)
        assert result == fake_payload


@pytest.mark.asyncio
async def test_get_current_active_user():
    fake_token = "fake.jwt.token"

    fake_user = {
        "_id": "64b8c8d1f1e2a3b4c5d6e7f8",
        "fullname": "John Doe",
        "email": "john@example.com",
        "role": "user",
        "status": "active"
    }

    fake_token_data = TokenData(sub="64b8c8d1f1e2a3b4c5d6e7f8", role="user")
    
    mock_db = AsyncMock()
    mock_db.auth_database.find_one.return_value = fake_user
    
    with patch("api_certify.dependencies.db_mongo.get_database", return_value=mock_db), \
         patch("api_certify.dependencies.JWTManager.verify_and_decode_jwt", return_value=fake_token_data):
        user = await get_current_active_user(current_user=fake_token_data)
        assert user == fake_user


def test_require_roles_success():
    fake_user = {"role": "admin"}
    dependency = require_roles(["admin", "user"])
    
    result = dependency(current_user=fake_user)
    assert result == fake_user


def test_require_roles_forbidden():
    fake_user = {"role": "user"}
    dependency = require_roles(["admin"])
    
    with pytest.raises(HTTPException) as exc:
        dependency(current_user=fake_user)
    assert exc.value.status_code == 403

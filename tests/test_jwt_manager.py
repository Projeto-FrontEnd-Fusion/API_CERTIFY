import pytest
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from jose import jwt

from api_certify.core.security.jwt_manager import JWTManager, JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRES
from api_certify.models.auth_model import Role
from api_certify.models.jwt_model import TokenData


@pytest.fixture
def token_data():
    return TokenData(sub="1", role="admin")


@pytest.fixture
def temp_env(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "testsecret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRES", "30")
    
    return {
        "SECRET_KEY": "testsecret",
        "JWT_ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRES": 30
    }


def test_jwt(token_data, temp_env, monkeypatch):
    monkeypatch.setattr("api_certify.core.security.jwt_manager.JWT_SECRET_KEY", temp_env["SECRET_KEY"])
    monkeypatch.setattr("api_certify.core.security.jwt_manager.JWT_ALGORITHM", temp_env["JWT_ALGORITHM"])
    monkeypatch.setattr("api_certify.core.security.jwt_manager.ACCESS_TOKEN_EXPIRES", temp_env["ACCESS_TOKEN_EXPIRES"])
    
    token = JWTManager.create_jwt(token_data)
    print(token_data)
        
    assert isinstance(token.access_token, str)
    
    payload = JWTManager.verify_and_decode_jwt(token.access_token)
    
    
    assert payload["sub"] == "1"
    assert payload["role"] in Role
    assert payload["iss"] == "api_certify"
    assert payload["aud"] == "api_certify"
    assert payload["iat"] is not None
    assert payload["exp"] is not None


def test_verify_and_decode_jwt_invalid_signature(token_data, temp_env, monkeypatch):
    monkeypatch.setattr("api_certify.core.security.jwt_manager.JWT_SECRET_KEY", temp_env["SECRET_KEY"])
    monkeypatch.setattr("api_certify.core.security.jwt_manager.JWT_ALGORITHM", temp_env["JWT_ALGORITHM"])

    # gera token válido com outra secret
    wrong_token = jwt.encode(token_data.model_dump(), "WRONG_SECRET", algorithm=temp_env["JWT_ALGORITHM"])

    with pytest.raises(HTTPException) as exc:
        JWTManager.verify_and_decode_jwt(wrong_token)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Token invalido"


def test_verify_and_decode_jwt_expired(token_data, temp_env, monkeypatch):
    monkeypatch.setattr("api_certify.core.security.jwt_manager.JWT_SECRET_KEY", temp_env["SECRET_KEY"])
    monkeypatch.setattr("api_certify.core.security.jwt_manager.JWT_ALGORITHM", temp_env["JWT_ALGORITHM"])
    
    # cria token já expirado
    expired_payload = {
        "sub": "123",
        "user_id": 2,
        "exp": datetime.now(timezone.utc) - timedelta(seconds=10)
    }
    
    expired_token = jwt.encode(expired_payload, temp_env["SECRET_KEY"], algorithm=temp_env["JWT_ALGORITHM"])
    
    with pytest.raises(HTTPException) as exc:
        JWTManager.verify_and_decode_jwt(expired_token)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Token expirado"

import pytest
from datetime import timedelta
from api_certify.core.security import (
    create_access_token,
    decode_access_token,
    HashManager,
)


# ==========================================
# Token creation
# ==========================================


def test_create_token():
    token = create_access_token({"sub": "user@test.com", "email": "user@test.com"})

    assert isinstance(token, str)
    assert len(token) > 10


def test_create_token_missing_sub():
    with pytest.raises(ValueError, match="Claim obrigatória ausente: sub"):
        create_access_token({"email": "user@test.com"})


def test_create_token_missing_email():
    with pytest.raises(ValueError, match="Claim obrigatória ausente: email"):
        create_access_token({"sub": "123"})


def test_create_token_custom_expiration():
    token = create_access_token(
        {"sub": "123", "email": "user@test.com"},
        expires_delta=timedelta(minutes=5),
    )
    assert isinstance(token, str)


# ==========================================
# Token decode
# ==========================================


def test_decode_valid_token():
    token = create_access_token({"sub": "123", "email": "user@test.com"})
    payload = decode_access_token(token)

    assert payload is not None
    assert payload["sub"] == "123"
    assert payload["email"] == "user@test.com"


def test_decode_expired_token():
    token = create_access_token(
        {"sub": "123", "email": "user@test.com"},
        expires_delta=timedelta(seconds=-1),
    )
    payload = decode_access_token(token)

    assert payload is None


def test_decode_invalid_token():
    payload = decode_access_token("token.invalido.aqui")

    assert payload is None


# ==========================================
# HashManager
# ==========================================


def test_hash_password():
    hashed = HashManager.hash_password("SenhaSegura123!")

    assert isinstance(hashed, str)
    assert hashed != "SenhaSegura123!"


def test_verify_password_correct():
    hashed = HashManager.hash_password("SenhaSegura123!")
    result = HashManager.verify_password("SenhaSegura123!", hashed)

    assert result is True


def test_verify_password_wrong():
    hashed = HashManager.hash_password("SenhaSegura123!")
    result = HashManager.verify_password("SenhaErrada", hashed)

    assert result is False

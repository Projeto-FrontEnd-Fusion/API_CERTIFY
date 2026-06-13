from datetime import timedelta

import pytest

from api_certify.core.security import (
    HashManager,
    create_access_token,
    decode_access_token,
)

JWT_PAYLOAD = {
    "sub": "123",
    "email": "user@test.com",
    "role": "user",
}


# ==========================================
# Token creation
# ==========================================


def test_create_token():
    token = create_access_token(JWT_PAYLOAD)

    assert isinstance(token, str)
    assert len(token) > 10


def test_create_token_missing_sub():
    with pytest.raises(ValueError, match="Claim obrigatória ausente: sub"):
        create_access_token(
            {
                "email": "user@test.com",
                "role": "user",
            }
        )


def test_create_token_missing_email():
    with pytest.raises(ValueError, match="Claim obrigatória ausente: email"):
        create_access_token(
            {
                "sub": "123",
                "role": "user",
            }
        )


def test_create_token_missing_role():
    with pytest.raises(ValueError, match="Claim obrigatória ausente: role"):
        create_access_token(
            {
                "sub": "123",
                "email": "user@test.com",
            }
        )


def test_create_token_custom_expiration():
    token = create_access_token(
        JWT_PAYLOAD,
        expires_delta=timedelta(minutes=5),
    )

    assert isinstance(token, str)


# ==========================================
# Token decode
# ==========================================


def test_decode_valid_token():
    token = create_access_token(JWT_PAYLOAD)
    payload = decode_access_token(token)

    assert payload is not None
    assert payload["sub"] == JWT_PAYLOAD["sub"]
    assert payload["email"] == JWT_PAYLOAD["email"]
    assert payload["role"] == JWT_PAYLOAD["role"]


def test_decode_expired_token():
    token = create_access_token(
        JWT_PAYLOAD,
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
    password = "SenhaSegura123!"
    hashed = HashManager.hash_password(password)

    assert HashManager.verify_password(password, hashed) is True


def test_verify_password_wrong():
    hashed = HashManager.hash_password("SenhaSegura123!")

    assert HashManager.verify_password("SenhaErrada", hashed) is False

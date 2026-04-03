from api_certify.core.security import create_access_token


def test_create_token():

    token = create_access_token({"sub": "user@test.com", "email": "user@test.com"})

    assert isinstance(token, str)
    assert len(token) > 10

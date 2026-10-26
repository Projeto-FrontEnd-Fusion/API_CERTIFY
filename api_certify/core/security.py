import os
from datetime import datetime, timedelta, timezone

import uuid
import bcrypt
from dotenv import load_dotenv
import jwt
from jwt import InvalidTokenError as JWTError

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

if not SECRET_KEY:
    raise ValueError("SECRET_KEY não configurada no .env")

# Preserve Passlib's UTF-8/72-byte behavior for existing password hashes and
# the API's existing password contract (up to 100 characters).
BCRYPT_MAX_BYTES = 72


class HashManager:

    @staticmethod
    def hash_password(password: str) -> str:
        password_bytes = password.encode('utf-8')[:BCRYPT_MAX_BYTES]
        return bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12)).decode('ascii')

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        password_bytes = password.encode('utf-8')[:BCRYPT_MAX_BYTES]
        return bcrypt.checkpw(password_bytes, hashed_password.encode('ascii'))


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    required_claims = ["sub", "email", "role"]

    for claim in required_claims:
        if claim not in data:
            raise ValueError(f"Claim obrigatória ausente: {claim}")

    to_encode = data.copy()
    to_encode["type"] = "access"

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    required_claims = ["sub", "email"]

    for claim in required_claims:
        if claim not in data:
            raise ValueError(f"Claim obrigatória ausente: {claim}")

    to_encode = data.copy()
    to_encode["type"] = "refresh"
    to_encode["jti"] = str(uuid.uuid4())

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") == "refresh":
            return None
        return payload
    except JWTError:
        return None


def decode_refresh_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError:
        return None

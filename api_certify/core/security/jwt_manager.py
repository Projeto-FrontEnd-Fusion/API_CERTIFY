import os
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer

from dotenv import load_dotenv
from jose import jwt, ExpiredSignatureError, JWTError

from api_certify.models.jwt_model import TokenData, Token


load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRES = int(os.getenv("ACCESS_TOKEN_EXPIRES"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="")

class JWTManager:
    @staticmethod
    def create_jwt(data: TokenData) -> Token:
        datetime_now = datetime.now(timezone.utc)
        expiration_datetime = datetime_now + timedelta(minutes=ACCESS_TOKEN_EXPIRES)
        
        payload = {
            "sub": data.sub,
            "role": data.role.value,
            "iss": data.iss,
            "aud": data.aud,
            "iat": int(datetime_now.timestamp()),
            "exp": int(expiration_datetime.timestamp())
        }
        
        token_str = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return Token(
            access_token=token_str,
            expires_in= ACCESS_TOKEN_EXPIRES * 60
            )

    @staticmethod
    def verify_and_decode_jwt(token: str) -> TokenData:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM], audience="api_certify")
            return payload
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=401,
                detail="Token expirado"
                )
        except JWTError:
            raise HTTPException(
                status_code=401,
                detail="Token invalido"
                )

from api_certify.repositories.auth_repository import AuthRepository
from api_certify.models.auth_model import AuthUser, AuthUserLogin, AuthUserReponse

from jose import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from fastapi import HTTPException, status

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))


class AuthService:

    def __init__(self, auth_repository: AuthRepository):
        self.auth_repository = auth_repository

    async def create_auth_user(self, auth_data: AuthUser) -> AuthUserReponse:
        auth = await self.auth_repository.create(auth_data)
        return auth

    async def login_auth(self, auth_data: AuthUserLogin):
        """
        Faz login do usuário e retorna JWT
        """

        user = await self.auth_repository.login(auth_data)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="E-mail ou senha inválidos",
            )

        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        payload = {
            "sub": str(user.id),
            "email": user.email,
            "exp": expire,
        }

        access_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        return {"auth": user, "access_token": access_token, "token_type": "bearer"}

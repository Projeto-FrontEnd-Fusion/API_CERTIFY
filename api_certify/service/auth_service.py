from datetime import datetime, timedelta, timezone

from api_certify.repositories.auth_repository import AuthRepository
from api_certify.repositories.refresh_token_repository import RefreshTokenRepository
from api_certify.models.auth_model import (
    AuthUser,
    AuthUserLogin,
    AuthUserReponse,
    UpdateUserSchema,
)
from api_certify.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from fastapi import HTTPException, status


class AuthService:

    def __init__(
        self,
        auth_repository: AuthRepository,
        refresh_token_repository: RefreshTokenRepository,
    ):
        self.auth_repository = auth_repository
        self.refresh_token_repository = refresh_token_repository

    async def create_auth_user(self, auth_data: AuthUser) -> AuthUserReponse:
        auth = await self.auth_repository.create(auth_data)
        return auth

    async def login_auth(self, auth_data: AuthUserLogin):
        user = await self.auth_repository.login(auth_data)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="E-mail ou senha inválidos",
            )

        token_data = {"sub": str(user.id), "email": user.email}

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        # Persistir refresh token no banco
        expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        await self.refresh_token_repository.create(
            user_id=str(user.id),
            token=refresh_token,
            expires_at=expires_at,
        )

        return {
            "auth": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def refresh_access_token(self, refresh_token: str):
        # Decodificar o refresh token
        payload = decode_refresh_token(refresh_token)

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido ou expirado",
            )

        # Verificar se existe no banco e não foi revogado
        stored_token = await self.refresh_token_repository.find_valid_token(refresh_token)

        if not stored_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido ou expirado",
            )

        # Revogar o refresh token usado (rotação)
        await self.refresh_token_repository.revoke(refresh_token)

        # Gerar novos tokens
        token_data = {"sub": payload["sub"], "email": payload["email"]}

        new_access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)

        # Persistir novo refresh token
        expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        await self.refresh_token_repository.create(
            user_id=payload["sub"],
            token=new_refresh_token,
            expires_at=expires_at,
        )

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    async def logout(self, refresh_token: str):
        # Revogar o refresh token
        revoked = await self.refresh_token_repository.revoke(refresh_token)

        if not revoked:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token já foi revogado ou não existe",
            )

        return {"message": "Sessão encerrada com sucesso"}

    async def get_me(self, user_id: str) -> AuthUserReponse:
        return await self.auth_repository.get_user_by_id(user_id)

    async def update_user(
        self, user_id: str, update_data: UpdateUserSchema, current_user_id: str
    ) -> AuthUserReponse:
        if user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você só pode atualizar o seu próprio perfil",
            )

        return await self.auth_repository.update(user_id, update_data)

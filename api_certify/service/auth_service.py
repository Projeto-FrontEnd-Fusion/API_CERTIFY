import logging
import secrets
import string
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from api_certify.core.security import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    HashManager,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from api_certify.models.auth_model import (
    AuthUser,
    AuthUserLogin,
    AuthUserReponse,
    CompanyResponse,
    CompanyUser,
    UpdateUserSchema,
)

logger = logging.getLogger(__name__)
PASSWORD_RESET_CODE_TTL_MINUTES = 10
from api_certify.repositories.auth_repository import AuthRepository
from api_certify.repositories.refresh_token_repository import RefreshTokenRepository


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

    async def create_company_user(self, company_data: CompanyUser) -> CompanyResponse:
        company = await self.auth_repository.create_company(company_data)
        return company

    async def login_auth(self, auth_data: AuthUserLogin):
        user = await self.auth_repository.login(auth_data)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="E-mail ou senha inválidos",
            )

        token_data = {"sub": str(user.id), "email": user.email, "role": user.role}

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token({"sub": str(user.id), "email": user.email})

        # Persistir refresh token no banco
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=REFRESH_TOKEN_EXPIRE_DAYS
        )
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
        stored_token = await self.refresh_token_repository.find_valid_token(
            refresh_token
        )

        if not stored_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido ou expirado",
            )

        # Revogar o refresh token usado (rotação)
        await self.refresh_token_repository.revoke(refresh_token)

        # Buscar usuário para obter role atual
        try:
            user = await self.auth_repository.get_user_by_id(payload["sub"])
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não encontrado",
            )

        # Gerar novos tokens
        token_data = {
            "sub": payload["sub"],
            "email": payload["email"],
            "role": user.role,
        }

        new_access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(
            {"sub": payload["sub"], "email": payload["email"]}
        )

        # Persistir novo refresh token
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=REFRESH_TOKEN_EXPIRE_DAYS
        )
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

    def _generate_reset_code(self) -> str:
        return ''.join(secrets.choice(string.digits) for _ in range(6))

    def _send_password_reset_code(self, email: str, code: str) -> None:
        logger.info('Código de recuperação para %s: %s', email, code)

    async def forgot_password(self, email: str) -> dict:
        user = await self.auth_repository.get_user_by_email(email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Usuário não encontrado',
            )

        code = self._generate_reset_code()
        code_hash = HashManager.hash_password(code)
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=PASSWORD_RESET_CODE_TTL_MINUTES
        )

        await self.auth_repository.store_password_reset_code(
            user_id=str(user.id),
            code_hash=code_hash,
            expires_at=expires_at,
        )

        self._send_password_reset_code(email, code)

        return {"message": "Código de recuperação enviado"}

    async def verify_code(self, email: str, code: str) -> dict:
        user = await self.auth_repository.get_user_by_email(email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Usuário não encontrado',
            )

        result = await self.auth_repository.verify_password_reset_code(
            user_id=str(user.id),
            code=code,
        )

        if result.get('success') is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['message'],
            )

        return result

    async def reset_password(self, email: str, code: str, new_password: str) -> dict:
        user = await self.auth_repository.get_user_by_email(email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Usuário não encontrado',
            )

        result = await self.auth_repository.reset_password_with_code(
            user_id=str(user.id),
            code=code,
            new_password=new_password,
        )

        if result.get('success') is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['message'],
            )

        return result

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

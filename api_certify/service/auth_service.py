from api_certify.repositories.auth_repository import AuthRepository
from api_certify.models.auth_model import AuthUser, AuthUserLogin, AuthUserReponse, UpdateUserSchema
from api_certify.core.security import create_access_token
from fastapi import HTTPException, status


class AuthService:

    def __init__(self, auth_repository: AuthRepository):
        self.auth_repository = auth_repository

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

        access_token = create_access_token({
            "sub": str(user.id),
            "email": user.email,
        })

        return {"auth": user, "access_token": access_token, "token_type": "bearer"}

    async def update_user(
        self, user_id: str, update_data: UpdateUserSchema, current_user_id: str
    ) -> AuthUserReponse:
        if user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você só pode atualizar o seu próprio perfil",
            )

        return await self.auth_repository.update(user_id, update_data)

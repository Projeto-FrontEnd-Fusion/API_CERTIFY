from api_certify.repositories.auth_repository import AuthRepository
from api_certify.models.auth_model import (
  AuthUser,
  AuthUserLogin,
  AuthUserReponse,
  Role
)

from api_certify.models.jwt_model import Token, TokenData, TokenResponse
from api_certify.core.security.jwt_manager import JWTManager


class AuthService:
  def __init__(self, auth_repository : AuthRepository):
    self.auth_repository = auth_repository

  async def create_auth_user(self, auth_data : AuthUser) -> AuthUserReponse:
    auth = await self.auth_repository.create(auth_data)
    return auth

  async def login_auth(self, auth_data: AuthUserLogin) -> TokenResponse:
    auth = await self.auth_repository.login(auth_data)
    token = await self.generate_token(auth)
    response = {
      "user": auth,
      "access_token": token.access_token,
      "token_type": "bearer"
    }
    return response

  async def generate_token(self, data: AuthUserReponse) -> Token:
    token_data = TokenData(
      sub=data.id,
      role=Role(data.role)
    )
    token = JWTManager.create_jwt(token_data)
    return token

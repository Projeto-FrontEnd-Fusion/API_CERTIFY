from api_certify.repositories.auth_repository import AuthRepository
from api_certify.models.auth_model import AuthUser, AuthUserInDb
class AuthService:
  def __init__(self, auth_repository : AuthRepository):
    self.auth_repository = auth_repository
  
  async def create_auth_user(self, auth_data : AuthUser) -> AuthUserInDb:
    return await self.auth_repository.create(auth_data)
    

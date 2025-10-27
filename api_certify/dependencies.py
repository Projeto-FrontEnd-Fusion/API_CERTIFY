from api_certify.repositories.auth_repository import AuthRepository
from api_certify.service.auth_service import AuthService
from api_certify.core.database.mongodb import db_mongo

def get_auth_repository() -> AuthRepository:
  database = await db_mongo.get_database()
  return AuthRepository(database)

def get_auth_service() -> AuthService:
  repository = get_auth_repository()
  return AuthService(repository)
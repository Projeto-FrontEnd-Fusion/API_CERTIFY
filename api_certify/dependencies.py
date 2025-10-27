from fastapi import Depends
from api_certify.service.auth_service import AuthService
from api_certify.repositories.auth_repository import AuthRepository
from api_certify.core.database.mongodb import db_mongo

async def get_auth_repository() -> AuthRepository:
    database = await db_mongo.get_database()
    return AuthRepository(database)

def get_auth_service(
    repository: AuthRepository = Depends(get_auth_repository)
) -> AuthService:
    return AuthService(repository)
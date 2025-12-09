from typing import List
from bson import ObjectId

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from api_certify.core.database.mongodb import db_mongo
from api_certify.models.auth_model import AuthUserReponse
from api_certify.service.auth_service import AuthService
from api_certify.repositories.auth_repository import AuthRepository
from api_certify.service.certificate_service import CertificateService
from api_certify.repositories.certificate_repository import CertificateRepository

from api_certify.models.jwt_model import TokenData
from api_certify.core.security.jwt_manager import JWTManager


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login",
    description=(
        "Use um token JWT no formato:\n\n"
        "`Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.EXEMPLO123.ABCD`"
    )
)


async def get_auth_repository() -> AuthRepository:
    database = await db_mongo.get_database()
    return AuthRepository(database)

def get_auth_service(
    auth_repository: AuthRepository = Depends(get_auth_repository),
) -> AuthService:
    return AuthService(auth_repository)

     # primeira mudança: 
    # Adciona corretamente aqui a injeção de dependência do AuthRepository para o CertificateService
    # injetei também o AuthRepository aqui
    
async def get_certificate_repository() -> CertificateRepository:
    database = await db_mongo.get_database()
    return CertificateRepository(database)



def get_certificate_service(
    certificate_repository: CertificateRepository = Depends(get_certificate_repository),
    auth_repository : AuthRepository = Depends(get_auth_repository),
) -> CertificateService:
    return CertificateService(certificate_repository, auth_repository)


def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    payload = JWTManager.verify_and_decode_jwt(token)
    return payload


async def get_current_active_user(current_user: TokenData = Depends(get_current_user)) -> AuthUserReponse:
    database = await db_mongo.get_database()
    user = await database.auth_database.find_one({"_id": ObjectId(current_user["sub"])})

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Usuário não encontrado"
            )

    if user.get("status", "").lower() != "active":
        raise HTTPException(
            status_code=401,
            detail="Usuário não autenticado"
            )
    return user


def require_roles(allowed_roles: List[str]):
    def dependency(current_user=Depends(get_current_active_user)):
        if current_user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="Permissões insuficientes"
                )
        return current_user
    return dependency

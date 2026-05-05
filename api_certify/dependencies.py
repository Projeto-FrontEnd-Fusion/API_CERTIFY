from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from api_certify.core.database.mongodb import db_mongo
from api_certify.core.security import decode_access_token
from api_certify.service.auth_service import AuthService
from api_certify.repositories.auth_repository import AuthRepository
from api_certify.service.certificate_service import CertificateService
from api_certify.repositories.certificate_repository import CertificateRepository


security_scheme = HTTPBearer()


# ---------- JWT MIDDLEWARE ----------


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> dict:
    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )

    return payload


# ---------- AUTH ----------


async def get_auth_repository() -> AuthRepository:
    database = await db_mongo.get_database()
    return AuthRepository(database)


def get_auth_service(
    auth_repository: AuthRepository = Depends(get_auth_repository),
) -> AuthService:
    return AuthService(auth_repository)


# ---------- CERTIFICATE ----------


async def get_certificate_repository() -> CertificateRepository:
    database = await db_mongo.get_database()
    return CertificateRepository(database)


def get_certificate_service(
    certificate_repository: CertificateRepository = Depends(get_certificate_repository),
    auth_repository: AuthRepository = Depends(get_auth_repository),
) -> CertificateService:
    return CertificateService(certificate_repository, auth_repository)

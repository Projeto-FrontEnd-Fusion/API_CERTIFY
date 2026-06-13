from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api_certify.core.database.mongodb import db_mongo
from api_certify.core.security import decode_access_token
from api_certify.repositories.auth_repository import AuthRepository
from api_certify.repositories.certificate_repository import CertificateRepository
from api_certify.service.auth_service import AuthService
from api_certify.service.certificate_service import CertificateService
from api_certify.repositories.refresh_token_repository import RefreshTokenRepository
from api_certify.service.certificate_service import CertificateService
from api_certify.repositories.certificate_repository import CertificateRepository
from api_certify.service.event_service import EventService
from api_certify.repositories.event_repository import EventRepository


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


def require_role(*allowed_roles: str):

    async def role_checker(
        current_user: dict = Depends(get_current_user),
    ):

        role = current_user.get("role")

        # Admin possui acesso total
        if role == "admin":
            return current_user

        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado. Permissão insuficiente para esta ação.",
            )

        return current_user

    return role_checker


# ---------- AUTH ----------


async def get_auth_repository() -> AuthRepository:
    database = await db_mongo.get_database()
    return AuthRepository(database)


async def get_refresh_token_repository() -> RefreshTokenRepository:
    database = await db_mongo.get_database()
    return RefreshTokenRepository(database)


def get_auth_service(
    auth_repository: AuthRepository = Depends(get_auth_repository),
    refresh_token_repository: RefreshTokenRepository = Depends(get_refresh_token_repository),
) -> AuthService:
    return AuthService(auth_repository, refresh_token_repository)


# ---------- EVENT ----------


async def get_event_repository() -> EventRepository:
    database = await db_mongo.get_database()
    return EventRepository(database)


def get_event_service(
    event_repository: EventRepository = Depends(get_event_repository),
) -> EventService:
    return EventService(event_repository)


# ---------- CERTIFICATE ----------


async def get_certificate_repository() -> CertificateRepository:
    database = await db_mongo.get_database()
    return CertificateRepository(database)


def get_certificate_service(
    certificate_repository: CertificateRepository = Depends(get_certificate_repository),
    auth_repository: AuthRepository = Depends(get_auth_repository),
    event_repository: EventRepository = Depends(get_event_repository),
) -> CertificateService:
    return CertificateService(certificate_repository, auth_repository, event_repository)

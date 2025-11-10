from fastapi import Depends

from api_certify.core.database.mongodb import db_mongo
from api_certify.repositories.auth_repository import AuthRepository
from api_certify.repositories.certificate_repository import (
    CertificateRepository,
)
from api_certify.repositories.Institution_auth_repository import (
    InstitutionAuthRepository,
)
from api_certify.service.auth_service import AuthService
from api_certify.service.certificate_service import CertificateService
from api_certify.service.Institution_auth_service import InstitutionAuthService


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
    certificate_repository: CertificateRepository = Depends(
        get_certificate_repository
    ),
    auth_repository: AuthRepository = Depends(get_auth_repository),
) -> CertificateService:
    return CertificateService(certificate_repository, auth_repository)


async def get_instituition_auth_repository() -> InstitutionAuthRepository:
    database = await db_mongo.get_database()
    return InstitutionAuthRepository(database)


async def get_institution_auth_service(
    institution_auth_repository: InstitutionAuthRepository = Depends(
        get_instituition_auth_repository
    ),
) -> InstitutionAuthService:
    return InstitutionAuthService(institution_auth_repository)

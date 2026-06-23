from app.database import get_database  # ajuste se no seu projeto tiver outro path
from app.modules.auth.repositories.auth_repository import AuthRepository
from app.modules.auth.schemas.create_company import CreateCompany
from app.modules.auth.services.auth_service import AuthService
from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/api/v1/auth", tags=["Company"])


# 🔧 Dependency Injection (Repository)
def get_auth_repository(db: AsyncIOMotorDatabase = Depends(get_database)):
    return AuthRepository(db)


# 🔧 Dependency Injection (Service)
def get_auth_service(
    repo: AuthRepository = Depends(get_auth_repository),
):
    return AuthService(repo)


@router.post(
    "/signup/company",
    status_code=status.HTTP_201_CREATED,
    summary="Cadastro de Empresa",
    description="Cria uma conta corporativa com CNPJ e role 'empresa'",
)
async def signup_company(
    payload: CreateCompany, service: AuthService = Depends(get_auth_service)
):
    """
    Cadastro de empresa (instituição)
    """
    result = await service.signup_company(payload)
    return result

from fastapi import APIRouter, Depends, HTTPException
from api_certify.schemas.responses import SucessResponse
from api_certify.models.auth_institution_model import InstitutionAuth, InstitutionAuthLogin
from api_certify.service.Institution_auth_service import InstitutionAuthService
from api_certify.dependencies import get_institution_auth_service

institution_auth_routes = APIRouter(prefix='/institution', tags=['Institution'])


@institution_auth_routes.post('/auth/create', response_model=SucessResponse, status_code=201)
async def create_institution_auth(
    institution_data: InstitutionAuth,
    service: InstitutionAuthService = Depends(get_institution_auth_service),
):
    try:
        institution_auth = await service.create_institution(institution_data)
        return SucessResponse(
            success=True,
            message='Intituição Criada',
            data={'institution': institution_auth},
        )
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err))

@institution_auth_routes.post('/auth/login', response_model=SucessResponse, status_code=200)
async def login_institution_auth(
    institution_login_data : InstitutionAuthLogin,
    service: InstitutionAuthService = Depends(get_institution_auth_service)
):

    try:
        institution_login = await service.login_institution(institution_login_data)
        return SucessResponse(
            success = True,
            message="Acesso Autorizado",
            data={'institution': institution_login}
        )
    except Exception as err:
        raise HTTPException(status_code=409, detail=str(err))

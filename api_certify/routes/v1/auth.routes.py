from fastapi import APIRouter, Depends, HTTPException
from api_certify.schemas.responses import SucessResponse
from api_certify.models.auth_model import AuthUser, AuthUserInDb
from api_certify.service.auth_service import AuthService
from api_certify.dependencies import get_auth_service
auth_route = APIRouter(
  prefix='/auth', tags=["Auth"]
)

@auth_route.post('/', response_model=SucessResponse, status_code=201)
async def create_auth(auth_data : AuthUser, service : AuthService = Depends(get_auth_service)):
    try:
      auth = await service.create_auth_user(auth_data)
      return SucessResponse(
        success= True,
        message= "Usuário cadastrado com sucesso",
        data = {"auth" : auth}
      )
    except Exception as err:
      raise HTTPException('Falha ao Criar novo usuário')
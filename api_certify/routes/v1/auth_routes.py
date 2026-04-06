from fastapi import APIRouter, Depends, HTTPException
from api_certify.schemas.responses import SucessResponse
from api_certify.models.auth_model import AuthUser, AuthUserInDb
from api_certify.service.auth_service import AuthService, AuthUserLogin
from api_certify.dependencies import get_auth_service
auth_routes = APIRouter(
  prefix='/auth', tags=["Auth"]
)

@auth_routes.post('/signup', response_model=SucessResponse, status_code=201)
async def create_auth(auth_data : AuthUser, service : AuthService = Depends(get_auth_service)):
    try:
      auth = await service.create_auth_user(auth_data)
      return SucessResponse(
        success= True,
        message= "Usuário cadastrado com sucesso",
        data = {"auth" : auth}
      )
    except Exception as err:
       raise HTTPException(
            status_code=400, 
            detail=str(err)
        )

@auth_routes.post("/login", response_model=SucessResponse, status_code=200)
async def login_auth(auth_data: AuthUserLogin, service: AuthService = Depends(get_auth_service)):
    try:
        auth_login = await service.login_auth(auth_data)
        return SucessResponse(
            success=True,
            message="Sucesso no Login",
            data={"auth": auth_login}
        )
    
    except Exception as err:
        # Tratamento mais específico baseado na mensagem de erro
        error_message = str(err)
        
        if "Credenciais Inválidas" in error_message:
            raise HTTPException(
                status_code=401,  # Unauthorized - mais específico
                detail="Email ou senha incorretos"
            )
        elif "Email já cadastrado" in error_message:
            raise HTTPException(
                status_code=409,  # Conflict
                detail="Email já está em uso"
            )
        else:
            raise HTTPException(
                status_code=400,  # Bad Request
                detail=f"Erro no login: {error_message}"
            )
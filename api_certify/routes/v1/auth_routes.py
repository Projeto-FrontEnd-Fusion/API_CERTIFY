from fastapi import APIRouter, Depends, HTTPException
from api_certify.schemas.responses import SucessResponse
from api_certify.models.auth_model import AuthUser, UpdateUserSchema
from api_certify.service.auth_service import AuthService, AuthUserLogin
from api_certify.dependencies import get_auth_service, get_current_user

auth_routes = APIRouter(prefix="/auth", tags=["Auth"])


@auth_routes.post("/signup", response_model=SucessResponse, status_code=201)
async def create_auth(
    auth_data: AuthUser, service: AuthService = Depends(get_auth_service)
):
    try:
        auth = await service.create_auth_user(auth_data)

        return SucessResponse(
            success=True,
            message="Usuário cadastrado com sucesso",
            data={"auth": auth},
        )

    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err))


@auth_routes.post("/login", response_model=SucessResponse, status_code=200)
async def login_auth(
    auth_data: AuthUserLogin, service: AuthService = Depends(get_auth_service)
):
    try:
        auth_login = await service.login_auth(auth_data)

        return SucessResponse(
            success=True,
            message="Sucesso no Login",
            data=auth_login,
        )

    except Exception as err:

        error_message = str(err)

        if "Credenciais inválidas" in error_message:
            raise HTTPException(
                status_code=401,
                detail="Email ou senha incorretos",
            )

        elif "Email já cadastrado" in error_message:
            raise HTTPException(
                status_code=409,
                detail="Email já está em uso",
            )

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Erro no login: {error_message}",
            )


@auth_routes.put("/{user_id}", response_model=SucessResponse, status_code=200)
async def update_user(
    user_id: str,
    update_data: UpdateUserSchema,
    service: AuthService = Depends(get_auth_service),
    current_user: dict = Depends(get_current_user),
):
    try:
        updated = await service.update_user(
            user_id, update_data, current_user["sub"]
        )

        return SucessResponse(
            success=True,
            message="Dados atualizados com sucesso",
            data={"auth": updated},
        )

    except HTTPException:
        raise

    except Exception as err:
        error_message = str(err)

        if "não encontrado" in error_message:
            raise HTTPException(status_code=404, detail=error_message)

        elif "já cadastrado" in error_message:
            raise HTTPException(status_code=409, detail=error_message)

        else:
            raise HTTPException(status_code=400, detail=error_message)

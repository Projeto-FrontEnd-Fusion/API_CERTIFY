from fastapi import APIRouter, Depends, HTTPException

from api_certify.dependencies import get_auth_service, get_current_user
from api_certify.models.auth_model import (
    AuthUser,
    CompanyUser,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UpdateUserSchema,
    VerifyCodeRequest,
)
from api_certify.schemas.responses import SucessResponse
from api_certify.service.auth_service import AuthService, AuthUserLogin

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


@auth_routes.post(
    "/signup/company",
    response_model=SucessResponse,
    status_code=201,
)
async def create_company(
    company_data: CompanyUser,
    service: AuthService = Depends(get_auth_service),
):
    try:
        company = await service.create_company_user(company_data)

        return SucessResponse(
            success=True,
            message="Empresa cadastrada com sucesso",
            data={"auth": company},
        )

    except Exception as err:
        error_message = str(err)

        if "CNPJ já cadastrado" in error_message:
            raise HTTPException(
                status_code=409,
                detail="CNPJ já cadastrado",
            )

        if "Email já cadastrado" in error_message:
            raise HTTPException(
                status_code=409,
                detail="Email já cadastrado",
            )

        if "CNPJ inválido" in error_message:
            raise HTTPException(
                status_code=400,
                detail="CNPJ inválido",
            )

        raise HTTPException(
            status_code=400,
            detail=error_message,
        )


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


@auth_routes.post("/forgot-password", response_model=SucessResponse, status_code=200)
async def forgot_password(
    payload: ForgotPasswordRequest,
    service: AuthService = Depends(get_auth_service),
):
    try:
        result = await service.forgot_password(str(payload.email))
        return SucessResponse(success=True, message=result["message"])
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err))


@auth_routes.post("/verify-code", response_model=SucessResponse, status_code=200)
async def verify_code(
    payload: VerifyCodeRequest,
    service: AuthService = Depends(get_auth_service),
):
    try:
        result = await service.verify_code(str(payload.email), payload.code)
        return SucessResponse(success=True, message=result["message"])
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err))


@auth_routes.post("/reset-password", response_model=SucessResponse, status_code=200)
async def reset_password(
    payload: ResetPasswordRequest,
    service: AuthService = Depends(get_auth_service),
):
    try:
        result = await service.reset_password(
            str(payload.email),
            payload.code,
            payload.new_password,
        )
        return SucessResponse(success=True, message=result["message"])
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err))


@auth_routes.get("/me", response_model=SucessResponse, status_code=200)
async def get_me(
    current_user: dict = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    try:
        user = await service.get_me(current_user["sub"])

        return SucessResponse(
            success=True,
            message="Usuário autenticado",
            data={"auth": user},
        )

    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err))


@auth_routes.put("/{user_id}", response_model=SucessResponse, status_code=200)
async def update_user(
    user_id: str,
    update_data: UpdateUserSchema,
    service: AuthService = Depends(get_auth_service),
    current_user: dict = Depends(get_current_user),
):
    try:
        updated = await service.update_user(user_id, update_data, current_user["sub"])

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


@auth_routes.post("/refresh", response_model=SucessResponse, status_code=200)
async def refresh_token(
    body: dict,
    service: AuthService = Depends(get_auth_service),
):
    refresh_token = body.get("refresh_token")

    if not refresh_token:
        raise HTTPException(status_code=400, detail="refresh_token é obrigatório")

    result = await service.refresh_access_token(refresh_token)

    return SucessResponse(
        success=True,
        message="Token renovado com sucesso",
        data=result,
    )


@auth_routes.post("/logout", response_model=SucessResponse, status_code=200)
async def logout(
    body: dict,
    current_user: dict = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    refresh_token = body.get("refresh_token")

    if not refresh_token:
        raise HTTPException(status_code=400, detail="refresh_token é obrigatório")

    result = await service.logout(refresh_token)

    return SucessResponse(
        success=True,
        message=result["message"],
    )

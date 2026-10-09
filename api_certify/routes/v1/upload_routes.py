from fastapi import APIRouter, Depends, UploadFile, File

from api_certify.dependencies import get_current_user, get_auth_service
from api_certify.schemas.responses import SucessResponse
from api_certify.service.upload_service import UploadService

upload_routes = APIRouter(prefix="/upload", tags=["Upload"])


def get_upload_service() -> UploadService:
    return UploadService()


@upload_routes.post(
    "/logo",
    response_model=SucessResponse,
    status_code=200,
)
async def upload_logo(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    service: UploadService = Depends(get_upload_service),
):
    url = await service.upload_logo(current_user["sub"], file)

    return SucessResponse(
        success=True,
        message="Logo enviada com sucesso",
        data={"url": url},
    )


@upload_routes.post(
    "/signature",
    response_model=SucessResponse,
    status_code=200,
)
async def upload_signature(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    service: UploadService = Depends(get_upload_service),
):
    url = await service.upload_signature(current_user["sub"], file)

    return SucessResponse(
        success=True,
        message="Assinatura enviada com sucesso",
        data={"url": url},
    )


@upload_routes.post("/avatar", response_model=SucessResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    service: UploadService = Depends(get_upload_service),
    auth_service=Depends(get_auth_service),
):
    url = await service.upload_avatar(current_user["sub"], file)
    await auth_service.set_avatar(current_user["sub"], url)
    return SucessResponse(success=True, message="Foto atualizada com sucesso", data={"url": url})

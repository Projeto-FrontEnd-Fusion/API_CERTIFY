from fastapi import APIRouter, Depends, HTTPException

from api_certify.schemas.responses import SucessResponse
from api_certify.models.certificate_model import (
    CreateCertificate,
)
from api_certify.service.certificate_service import CertificateService
from api_certify.dependencies import get_certificate_service

certificate_routes = APIRouter(prefix="/certificate", tags=["Certificates"])


@certificate_routes.post("/{user_id}", response_model=SucessResponse, status_code=201)
async def request_certificate(
    user_id: str,
    payload: CreateCertificate,
    service: CertificateService = Depends(get_certificate_service),
):
    try:
        certificate = await service.create_participant_certificate(user_id, payload)
        return SucessResponse(
            success=True,
            message="Certificado criado com sucesso.",
            data={"certificate": certificate},
        )
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err))


@certificate_routes.get("/users/{user_id}", response_model=SucessResponse, status_code=200)
async def get_many_certificate(
    user_id: str, service: CertificateService = Depends(get_certificate_service)
):
    try:
        certificates = await service.get_many_certificates(user_id)
        return SucessResponse(
            success=True,
            message="Certificados obtidos com sucesso.",
            data={"certificates": certificates},
        )
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err))


@certificate_routes.get("/{item_id}", response_model=SucessResponse, status_code=200)
async def get_certificate_by_id(
    item_id: str,
    service: CertificateService = Depends(get_certificate_service),
):
    try:
        certificate = await service.get_certificate_by_id(item_id)
        return SucessResponse(
            success=True,
            message="Certificado obtido com sucesso.",
            data={"certificate": certificate},
        )
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err))

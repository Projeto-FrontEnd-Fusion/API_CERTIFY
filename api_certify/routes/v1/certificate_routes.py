from fastapi import APIRouter, Depends, HTTPException

from api_certify.schemas.responses import SucessResponse
from api_certify.models.certificate_model import CreateCertificate
from api_certify.service.certificate_service import CertificateService
from api_certify.dependencies import get_certificate_service


certificate_routes = APIRouter(prefix="/certificate", tags=["Certificates"])


# ================================
# Criar certificado
# ================================
@certificate_routes.post("/{user_id}", response_model=SucessResponse, status_code=201)
async def request_certificate(
    user_id: str,
    payload: CreateCertificate,
    service: CertificateService = Depends(get_certificate_service),
):
    certificate = await service.create_participant_certificate(user_id, payload)

    return SucessResponse(
        success=True,
        message="Certificado criado com sucesso.",
        data={"certificate": certificate},
    )


# ================================
# Listar certificados do usuário
# ================================
@certificate_routes.get(
    "/users/{user_id}", response_model=SucessResponse, status_code=200
)
async def get_many_certificate(
    user_id: str,
    service: CertificateService = Depends(get_certificate_service),
):
    certificates = await service.get_many_certificates(user_id)

    return SucessResponse(
        success=True,
        message="Certificados obtidos com sucesso.",
        data={"certificates": certificates},
    )


# ================================
# Validação pública de certificado
# ================================
@certificate_routes.get(
    "/validate/{access_key}", response_model=SucessResponse, status_code=200
)
async def validate_certificate(
    access_key: str,
    service: CertificateService = Depends(get_certificate_service),
):
    certificate = await service.validate_certificate(access_key)

    if not certificate:
        raise HTTPException(status_code=404, detail="Certificado não encontrado")

    return SucessResponse(
        success=True,
        message="Certificado validado com sucesso.",
        data={"certificate": certificate},
    )


# ================================
# Buscar certificado por ID
# ================================
@certificate_routes.get("/{item_id}", response_model=SucessResponse, status_code=200)
async def get_certificate_by_id(
    item_id: str,
    service: CertificateService = Depends(get_certificate_service),
):
    certificate = await service.get_certificate_by_id(item_id)

    if not certificate:
        raise HTTPException(status_code=404, detail="Certificado não encontrado")

    return SucessResponse(
        success=True,
        message="Certificado obtido com sucesso.",
        data={"certificate": certificate},
    )

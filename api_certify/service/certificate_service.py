from api_certify.repositories.certificate_repository import CertificateRepository
from api_certify.models.certificate_model import (
    CertificateResponse,
    CreateCertificate,
)


class CertificateService:
    def __init__(self, certificate_repository: CertificateRepository):
        self.certificate_repository = certificate_repository

    async def create_participant_certificate(
        self, user_id: str, certificate_data: CreateCertificate
    ) -> CertificateResponse:
        certificate = await self.certificate_repository.create(
            user_id, certificate_data
        )
        return certificate

    async def get_many_certificates(self, user_id: str) -> list[CertificateResponse]:
        certificates = await self.certificate_repository.get_many_certificates(user_id)
        return certificates

    async def get_certificate_by_id(self, certificate_id: str):
        response = await self.certificate_repository.get_certificate(certificate_id)
        return response

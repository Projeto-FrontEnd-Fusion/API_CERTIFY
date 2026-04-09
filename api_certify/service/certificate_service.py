from fastapi import HTTPException, status

from api_certify.repositories.certificate_repository import CertificateRepository
from api_certify.repositories.auth_repository import AuthRepository

from api_certify.models.certificate_model import (
    CertificateInDb,
    CreateCertificate,
)


class CertificateService:

    def __init__(
        self,
        certificate_repository: CertificateRepository,
        auth_repository: AuthRepository,
    ):
        self.certificate_repository = certificate_repository
        self.auth_repository = auth_repository

    # =====================================
    # Criar certificado
    # =====================================

    async def create_participant_certificate(
        self, user_id: str, certificate_data: CreateCertificate
    ) -> CertificateInDb:

        # Verifica se usuário existe
        is_existing_user = await self.auth_repository.isExistAuth(user_id)

        if not is_existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não existe, certificado não pode ser criado",
            )

        # Verifica se já existe certificado para esse evento
        existing_certificate = (
            await self.certificate_repository.find_existing_certificate(
                user_id, certificate_data
            )
        )

        if existing_certificate:
            return existing_certificate

        # Cria novo certificado
        return await self.certificate_repository.create(user_id, certificate_data)

    # =====================================
    # Listar certificados do usuário
    # =====================================

    async def get_many_certificates(self, user_id: str) -> list[CertificateInDb]:

        return await self.certificate_repository.get_many_certificates(user_id)

    # =====================================
    # Buscar certificado por ID
    # =====================================

    async def get_certificate_by_id(self, certificate_id: str) -> CertificateInDb:

        certificate = await self.certificate_repository.get_certificate(certificate_id)

        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Certificado não encontrado",
            )

        return certificate

    # =====================================
    # Validação pública de certificado
    # =====================================

    async def validate_certificate(self, access_key: str) -> dict:

        certificate = await self.certificate_repository.get_certificate_by_access_key(
            access_key
        )

        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Certificado não encontrado",
            )

        # regra de negócio: certificado precisa estar disponível
        if certificate.status != "available":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Certificado não disponível",
            )

        return {
            "participant_name": certificate.participant_name,
            "event_name": certificate.event_name,
            "workload": certificate.workload,
            "issued_at": certificate.issued_at,
        }

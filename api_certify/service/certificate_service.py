from fastapi import HTTPException, status

from api_certify.models.certificate_model import CertificateInDb, CreateCertificate
from api_certify.repositories.auth_repository import AuthRepository
from api_certify.repositories.certificate_repository import CertificateRepository
from api_certify.repositories.event_repository import EventRepository
from api_certify.schemas.responses import CertificateValidationResponse


class CertificateService:

    def __init__(
        self,
        certificate_repository: CertificateRepository,
        auth_repository: AuthRepository,
        event_repository: EventRepository,
    ):
        self.certificate_repository = certificate_repository
        self.auth_repository = auth_repository
        self.event_repository = event_repository

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

        # Verifica se o evento existe
        event_exists = await self.event_repository.exists(certificate_data.event_id)

        if not event_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento não encontrado. Não é possível emitir certificado para um evento inexistente.",
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

    async def get_many_certificates(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 20,
    ):
        skip = (page - 1) * limit

        return await self.certificate_repository.get_many_certificates(
            user_id=user_id,
            skip=skip,
            limit=limit,
            page=page,
        )

    # =====================================
    # Buscar certificado por ID
    # =====================================

    async def get_certificate_by_id(self, certificate_id: str) -> CertificateInDb:
        response = await self.certificate_repository.get_certificate(certificate_id)
        return response

    async def validate_certificate(
        self, access_key: str
    ) -> CertificateValidationResponse:
        doc = await self.certificate_repository.find_by_access_key(access_key)
        if not doc:
            raise Exception("Certificado não encontrado ou código inválido.")
        return CertificateValidationResponse(
            participant_name=doc["participant_name"],
            event_name=doc["event_name"],
            workload=doc["workload"],
            issued_at=doc.get("issued_at"),
            event_start=doc.get("event_start"),
            event_end=doc.get("event_end"),
        )

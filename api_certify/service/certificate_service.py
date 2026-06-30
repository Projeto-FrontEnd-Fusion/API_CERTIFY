import asyncio

from fastapi import HTTPException, status

from api_certify.models.certificate_model import (
    BatchCertificateRequest,
    BatchCertificateSummary,
    CertificateInDb,
    CreateCertificate,
    Status,
)
from api_certify.repositories.auth_repository import AuthRepository
from api_certify.repositories.certificate_repository import (
    ACCESS_KEY,
    CertificateRepository,
)
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

        is_existing_user = await self.auth_repository.isExistAuth(user_id)

        if not is_existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não existe, certificado não pode ser criado",
            )

        event_exists = await self.event_repository.exists(certificate_data.event_id)

        if not event_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento não encontrado. Não é possível emitir certificado para um evento inexistente.",
            )

        event_data = None
        if hasattr(self.event_repository, "find_by_id"):
            event_data = await self.event_repository.find_by_id(
                certificate_data.event_id
            )

        event_payload = None
        if event_data is not None and hasattr(event_data, "model_dump"):
            event_payload = event_data.model_dump()
        elif event_data is not None:
            event_payload = dict(event_data)

        existing_certificate = (
            await self.certificate_repository.find_existing_certificate(
                user_id, certificate_data
            )
        )

        if existing_certificate:
            return existing_certificate

        return await self.certificate_repository.create(
            user_id,
            certificate_data,
            event_data=event_payload,
        )

    async def create_batch_certificates(
        self, payload: dict | BatchCertificateRequest
    ) -> BatchCertificateSummary:
        if isinstance(payload, dict):
            payload = BatchCertificateRequest(**payload)

        if len(payload.participants) > 200:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="O limite máximo é de 200 participantes por requisição.",
            )

        event_exists = await self.event_repository.exists(payload.event_id)
        if not event_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento não encontrado. Não é possível emitir certificados para um evento inexistente.",
            )

        event_data = None
        if hasattr(self.event_repository, "find_by_id"):
            event_data = await self.event_repository.find_by_id(payload.event_id)

        event_payload = None
        if event_data is not None and hasattr(event_data, "model_dump"):
            event_payload = event_data.model_dump()
        elif event_data is not None:
            event_payload = dict(event_data)

        async def _create_one(participant):
            try:
                existing_certificate = (
                    await self.certificate_repository.find_existing_certificate_by_email(
                        payload.event_id,
                        participant.email,
                    )
                )
                if existing_certificate:
                    return "duplicate"

                user_lookup = await self.auth_repository.find_by_email(
                    participant.email
                )
                if isinstance(user_lookup, dict):
                    user_id = user_lookup.get("_id") or user_lookup.get("id")
                else:
                    user_id = getattr(user_lookup, "id", None)

                if not user_id:
                    user_id = f"guest:{participant.email}"

                certificate_data = CreateCertificate(
                    fullname=participant.fullname,
                    access_key=ACCESS_KEY,
                    event_id=payload.event_id,
                    status=Status.AVAILABLE,
                    email=participant.email,
                )

                await self.certificate_repository.create(
                    user_id,
                    certificate_data,
                    event_data=event_payload,
                )
                return "created"
            except Exception:
                return "error"

        results = await asyncio.gather(
            *[_create_one(participant) for participant in payload.participants]
        )

        summary = {
            "total_enviados": len(payload.participants),
            "criados": results.count("created"),
            "duplicados_ignorados": results.count("duplicate"),
            "erros": results.count("error"),
        }

        return BatchCertificateSummary(**summary)

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

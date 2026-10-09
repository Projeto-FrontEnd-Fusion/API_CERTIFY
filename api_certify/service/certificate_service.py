import asyncio
from datetime import datetime, timezone
from bson import ObjectId
from urllib.parse import urlparse

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
        email_service=None,
    ):
        self.certificate_repository = certificate_repository
        self.auth_repository = auth_repository
        self.event_repository = event_repository
        self.email_service = email_service

    # =====================================
    # Criar certificado
    # =====================================

    async def create_participant_certificate(
        self,
        user_id: str,
        certificate_data: CreateCertificate,
        issuer_id: str | None = None,
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
            issuer_id=issuer_id,
            event_data=event_payload,
        )

    async def create_batch_certificates(
        self, payload: dict | BatchCertificateRequest, issuer_id: str | None = None
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
                    issuer_id=issuer_id,
                    event_data=event_payload,
                    notify_students=payload.notify_students,
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

    async def get_certificates_by_issuer(
        self,
        empresa_id: str,
        page: int = 1,
        limit: int = 20,
        event_id: str | None = None,
        status: str | None = None,
    ):
        skip = (page - 1) * limit

        return await self.certificate_repository.get_certificates_by_issuer(
            empresa_id=empresa_id,
            skip=skip,
            limit=limit,
            page=page,
            event_id=event_id,
            status=status,
        )

    async def update_certificate_status(
        self,
        certificate_id: str,
        status: str,
    ) -> CertificateInDb:
        normalized_status = self._normalize_status(status)

        certificate = await self.certificate_repository.update_status(
            certificate_id=certificate_id,
            status=normalized_status,
        )

        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Certificado não encontrado.",
            )

        return certificate

    def _normalize_status(self, status: str) -> str:
        normalized_status = (status or "").strip().lower()

        if normalized_status in {"active", "available"}:
            return "available"

        if normalized_status in {"inactive", "disabled"}:
            return "inactive"

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Status inválido. Use 'active' ou 'inactive'.",
        )

    async def validate_certificate(
        self, access_key: str
    ) -> CertificateValidationResponse:
        doc = await self.certificate_repository.find_by_access_key(access_key)
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Certificado não encontrado ou código inválido.",
            )
        expiry = doc.get('valid_until')
        if expiry:
            if isinstance(expiry, str):
                expiry = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
            expires_at = expiry.replace(tzinfo=expiry.tzinfo or timezone.utc)
            if expires_at <= datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=404, detail='Certificado expirado.'
                )
        return CertificateValidationResponse(
            access_key=access_key,
            institution_name=doc.get('institution_name', ''),
            description=doc.get('description', ''),
            valid_until=doc.get('valid_until'),
            design=doc.get('design') or {},
            participant_name=doc["participant_name"],
            event_name=doc["event_name"],
            workload=doc["workload"],
            issued_at=doc.get("issued_at"),
            event_start=doc.get("event_start"),
            event_end=doc.get("event_end"),
        )

    async def send_pending_notifications(self):
        if self.email_service is not None:
            await self.email_service.dispatch_pending()

    async def send_links(self, certificate_ids: list[str], current_user: dict):
        ids = list(dict.fromkeys(certificate_ids))
        if any(not ObjectId.is_valid(item) for item in ids):
            raise HTTPException(
                status_code=422, detail='ID de certificado inválido.'
            )
        collection = self.certificate_repository.certificate_collection
        object_ids = [ObjectId(item) for item in ids]
        docs = await collection.find({'_id': {'$in': object_ids}}).to_list(
            length=200
        )
        if len(docs) != len(ids):
            raise HTTPException(
                status_code=404, detail='Certificado não encontrado.'
            )
        for doc in docs:
            owner = (
                doc.get('issuer_id')
                if current_user.get('role') == 'empresa'
                else doc.get('user_id')
            )
            if current_user.get('role') != 'admin' and owner != current_user.get(
                'sub'
            ):
                raise HTTPException(status_code=403, detail='Acesso negado.')
            expiry = doc.get('valid_until')
            if doc.get('status') != 'available' or (
                expiry
                and expiry.replace(tzinfo=expiry.tzinfo or timezone.utc)
                <= datetime.now(timezone.utc)
            ):
                raise HTTPException(
                    status_code=409, detail='Certificado indisponível para envio.'
                )
        email = self.email_service
        if email is None or not email.transport.host or not email.transport.sender:
            raise HTTPException(
                status_code=503, detail='Serviço de e-mail não configurado.'
            )
        url = urlparse(email.frontend_url)
        if url.scheme not in {'http', 'https'} or not url.netloc:
            raise HTTPException(
                status_code=503, detail='URL do frontend não configurada.'
            )
        await collection.update_many(
            {
                '_id': {'$in': object_ids},
                'notifications.student.status': {'$in': ['deferred', 'failed']},
            },
            {'$set': {'notifications.student.status': 'pending'}},
        )
        await collection.update_many(
            {
                '_id': {'$in': object_ids},
                'notifications.student.status': {'$exists': False},
            },
            {
                '$set': {
                    'notifications.student': {'status': 'pending', 'attempts': 0}
                }
            },
        )
        await email.dispatch_pending(
            certificate_ids=object_ids, audiences=('student',)
        )
        docs = await collection.find({'_id': {'$in': object_ids}}).to_list(
            length=200
        )
        states = [
            doc.get('notifications', {}).get('student', {}).get('status')
            for doc in docs
        ]
        return {
            'total': len(ids),
            'sent': states.count('sent'),
            'failed': states.count('failed'),
            'pending': len(ids) - states.count('sent') - states.count('failed'),
        }

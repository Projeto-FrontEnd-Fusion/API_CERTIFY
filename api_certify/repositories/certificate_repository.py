import math
import os
import uuid
from datetime import datetime, timedelta, timezone

from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo import ReturnDocument

from api_certify.models.certificate_model import CertificateInDb, CreateCertificate

ACCESS_KEY = os.getenv("ACCESS_KEY")

if not ACCESS_KEY or ACCESS_KEY.strip() == "":
    raise RuntimeError(
        "Erro de Configuração: ACCESS_KEY não encontrada no ambiente. "
        "O servidor não pode ser iniciado."
    )


def add_years(data: datetime, anos: int) -> datetime:
    try:
        return data.replace(year=data.year + anos)
    except ValueError:
        return data.replace(month=2, day=28, year=data.year + anos)


def build_certificate(
    userId: str,
    participantName: str,
    participantEmail: str,
    access_key: str,
    status: str,
    issuer_id: str | None = None,
    event_data: dict | None = None,
) -> dict:
    now = datetime.now(timezone.utc)

    if not event_data:
        raise ValueError(
            'Dados do evento são obrigatórios para emitir certificados.'
        )

    event_id = str(event_data.get('id') or event_data.get('_id') or '')
    event_name = (
        event_data.get('name') or event_data.get('event_name') or 'Evento'
    )
    institution_name = (
        event_data.get('institution')
        or event_data.get('institution_name')
        or ''
    )
    description = event_data.get('description') or 'Participou do evento.'
    workload = str(event_data.get('workload') or '')
    event_start = event_data.get('start_date')
    event_end = event_data.get('end_date')
    event_date = event_data.get('start_date')

    result = {
        'user_id': str(userId),
        'access_key': access_key,
        'status': status,
        'participant_name': participantName,
        'participant_email': participantEmail,
        'institution_name': institution_name,
        'event_id': event_id,
        'event_name': event_name,
        'description': description,
        'workload': workload,
        'event_start': event_start,
        'event_end': event_end,
        'event_date': event_date,
        'issued_at': now,
        'valid_until': add_years(now, 2),
        'design': event_data.get('design') or {},
    }

    validity = (event_data.get('design') or {}).get('validity')
    durations = {
        '30 dias': 30,
        '90 dias': 90,
        '6 meses': 180,
        '1 ano': 365,
        '2 anos': 730,
    }
    if validity == 'Sem validade':
        result['valid_until'] = None
    elif validity in durations:
        result['valid_until'] = now + timedelta(days=durations[validity])

    if issuer_id is not None:
        result['issuer_id'] = issuer_id

    return result


class CertificateRepository:

    def __init__(self, database: AsyncIOMotorDatabase):

        self.certificate_collection: AsyncIOMotorCollection = database.get_collection(
            "certificates"
        )

        self.auth_collection: AsyncIOMotorCollection = database.get_collection(
            "auth_database"
        )

    # ========================================
    # Busca certificado existente
    # ========================================

    async def find_existing_certificate(
        self, user_id: str, certificate_data: CreateCertificate
    ) -> CertificateInDb | None:

        existing_certificate = await self.certificate_collection.find_one(
            {
                "user_id": user_id,
                "event_id": certificate_data.event_id,
            }
        )

        if existing_certificate:
            existing_certificate["_id"] = str(existing_certificate["_id"])
            return CertificateInDb(**existing_certificate)

        return None

    async def find_existing_certificate_by_email(
        self, event_id: str, email: str
    ) -> CertificateInDb | None:
        normalized_email = email.strip().lower()

        existing_certificate = await self.certificate_collection.find_one(
            {
                "participant_email": normalized_email,
                "event_id": event_id,
            }
        )

        if existing_certificate:
            existing_certificate["_id"] = str(existing_certificate["_id"])
            return CertificateInDb(**existing_certificate)

        return None

    # ========================================
    # Criar certificado
    # ========================================

    async def create(
        self,
        user_id: str,
        certificate_data: CreateCertificate,
        issuer_id: str | None = None,
        event_data: dict | None = None,
        notify_students: bool = True,
    ) -> CertificateInDb:

        if certificate_data.access_key != ACCESS_KEY:
            raise Exception("Chave de acesso inválida.")

        existing = await self.find_existing_certificate(user_id, certificate_data)

        if existing:
            return existing

        created_certificate = build_certificate(
            userId=user_id,
            participantEmail=certificate_data.email,
            participantName=certificate_data.fullname,
            access_key=str(uuid.uuid4()),
            status="available",
            issuer_id=issuer_id,
            event_data=event_data,
        )

        created_certificate['notifications'] = {
            'student': {
                'status': 'pending' if notify_students else 'deferred',
                'attempts': 0,
            },
            'company': {'status': 'pending' if issuer_id else 'skipped', 'attempts': 0},
        }
        result = await self.certificate_collection.insert_one(created_certificate)

        created_doc = await self.certificate_collection.find_one(
            {"_id": result.inserted_id}
        )

        if not created_doc:
            raise Exception("Erro ao criar o certificado.")

        await self.auth_collection.find_one_and_update(
            {"email": certificate_data.email},
            {"$set": {"status": "available"}},
        )

        created_doc["_id"] = str(created_doc["_id"])

        return CertificateInDb(**created_doc)

    # ========================================
    # Buscar certificados do usuário
    # ========================================

    async def get_many_certificates(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
        page: int = 1,
    ) -> list[CertificateInDb]:
        existing_user = await self.auth_collection.find_one({"_id": ObjectId(user_id)})

        if not existing_user:
            raise Exception("Usuário não encontrado")

        filter_query = {"user_id": user_id}

        total = await self.certificate_collection.count_documents(filter_query)

        cursor = (
            self.certificate_collection.find(filter_query)
            .sort("issued_at", -1)
            .skip(skip)
            .limit(limit)
        )

        docs = await cursor.to_list(length=limit)

        for doc in docs:
            doc["_id"] = str(doc["_id"])

        certificates = [CertificateInDb(**doc) for doc in docs]

        total_pages = math.ceil(total / limit) if total > 0 else 0

        return {
            "items": certificates,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
        }

    # ========================================
    # Buscar certificados por emissor
    # ========================================

    async def get_certificates_by_issuer(
        self,
        empresa_id: str,
        skip: int = 0,
        limit: int = 20,
        page: int = 1,
        event_id: str | None = None,
        status: str | None = None,
    ) -> dict:

        filter_query = {
            "$or": [
                {"institution_name": empresa_id},
                {"issuer_id": empresa_id},
            ]
        }

        if event_id:
            filter_query["event_id"] = event_id

        if status:
            filter_query["status"] = status

        total = await self.certificate_collection.count_documents(filter_query)

        cursor = (
            self.certificate_collection.find(filter_query)
            .sort("issued_at", -1)
            .skip(skip)
            .limit(limit)
        )

        docs = await cursor.to_list(length=limit)

        for doc in docs:
            doc["_id"] = str(doc["_id"])

        certificates = [CertificateInDb(**doc) for doc in docs]

        total_pages = math.ceil(total / limit) if total > 0 else 0

        return {
            "items": certificates,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
        }

    # ========================================
    # Buscar certificado por ID
    # ========================================

    async def get_certificate(self, certificate_id: str) -> CertificateInDb:

        if not ObjectId.is_valid(certificate_id):
            return None

        existingCertificate = await self.certificate_collection.find_one(
            {"_id": ObjectId(certificate_id)}
        )

        if not existingCertificate:
            return None

        existingCertificate["_id"] = str(existingCertificate["_id"])

        return CertificateInDb(**existingCertificate)

    async def update_status(self, certificate_id: str, status: str) -> CertificateInDb | None:
        updated_doc = await self.certificate_collection.find_one_and_update(
            {"_id": ObjectId(certificate_id)},
            {"$set": {"status": status}},
            return_document=ReturnDocument.AFTER,
        )

        if not updated_doc:
            return None

        updated_doc["_id"] = str(updated_doc["_id"])
        return CertificateInDb(**updated_doc)

    # ========================================
    # Buscar certificado por access_key
    # (USADO NA VALIDAÇÃO PÚBLICA)
    # ========================================

    async def find_by_access_key(self, access_key: str) -> dict | None:
        doc = await self.certificate_collection.find_one(
            {
                "access_key": access_key,
                "status": {"$in": ["available", "pending"]},
            }
        )
        return doc

import math
import os
import uuid
from datetime import datetime, timezone

from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

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


def mocked_certificate(
    userId: str,
    participantName: str,
    participantEmail: str,
    access_key: str,
    status: str,
    event_data: dict | None = None,
) -> dict:

    now = datetime.now(timezone.utc)
    format = "%Y-%m-%dT%H:%M:%S.%fZ"

    if event_data is None:
        event_data = {
            "id": "1",
            "name": "Imersão Dev Insights",
            "institution": "Comunidade Frontend Fusion",
            "description": "Participou da Imersão Dev Insights.",
            "workload": 9,
            "start_date": datetime.strptime("2025-11-05T00:00:00.000Z", format),
            "end_date": datetime.strptime("2025-11-07T00:00:00.000Z", format),
        }

    event_id = str(event_data.get("id") or event_data.get("_id") or "1")
    event_name = event_data.get("name") or event_data.get("event_name") or "Evento"
    institution_name = (
        event_data.get("institution")
        or event_data.get("institution_name")
        or "Comunidade Frontend Fusion"
    )
    description = event_data.get("description") or "Participou do evento."
    workload = str(event_data.get("workload") or "9")
    event_start = event_data.get("start_date")
    event_end = event_data.get("end_date")
    event_date = event_data.get("start_date")

    result = {
        "user_id": str(userId),
        "access_key": access_key,
        "status": status,
        "participant_name": participantName,
        "participant_email": participantEmail,
        "institution_name": institution_name,
        "event_id": event_id,
        "event_name": event_name,
        "description": description,
        "workload": workload,
        "event_start": event_start,
        "event_end": event_end,
        "event_date": event_date,
        "issued_at": now,
        "valid_until": add_years(now, 2),
    }

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
        event_data: dict | None = None,
    ) -> CertificateInDb:

        if certificate_data.access_key != ACCESS_KEY:
            raise Exception("Chave de acesso inválida.")

        existing = await self.find_existing_certificate(user_id, certificate_data)

        if existing:
            return existing

        created_certificate = mocked_certificate(
            userId=user_id,
            participantEmail=certificate_data.email,
            participantName=certificate_data.fullname,
            access_key=str(uuid.uuid4()),
            status="available",
            event_data=event_data,
        )

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
    # Buscar certificado por ID
    # ========================================

    async def get_certificate(self, certificate_id: str) -> CertificateInDb:

        existingCertificate = await self.certificate_collection.find_one(
            {"_id": ObjectId(certificate_id)}
        )

        if not existingCertificate:
            raise Exception("Certificado não encontrado.")

        existingCertificate["_id"] = str(existingCertificate["_id"])

        return CertificateInDb(**existingCertificate)

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

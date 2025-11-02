from datetime import datetime, timezone
import uuid
from bson.objectid import ObjectId

from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection

from api_certify.models.certificate_model import (
    CertificateResponse,
    CreateCertificate,
    Status,
)


def add_years(data: datetime, anos: int) -> datetime:
    """Adiciona um número de anos a uma data, ajustando para anos não bissextos se necessário."""
    try:
        return data.replace(year=data.year + anos)
    except ValueError:
        # Caso especial: 29 de fevereiro → ajusta para 28 de fevereiro
        return data.replace(month=2, day=28, year=data.year + anos)


def mocked_event(userId, participantName, participantEmail):
    now = datetime.now(timezone.utc)
    format = "%Y-%m-%dT%H:%M:%S.%fZ"

    result = {
        "_id": "dinamico",
        "user_id": str(userId),
        "access_key": "DEV25",
        "status": "avaliable",
        "participant_name": participantName,
        "participant_email": participantEmail,
        "institution_name": "Comunidade Frontend Fusion",
        "event_id": "1",
        "event_name": "Imersão Dev Insights",
        "description": "Participou da Imersão Dev Insights, realizada nos dias 5, 6 e 7 de novembro, um evento voltado ao aprendizado, conexão e desenvolvimento em gestão de produtos e metodologias ágeis. Durante esta imersão, o(a) participante teve contato com conteúdos ministrados por profissionais experientes, desenvolvendo habilidades essenciais para atuar em ambientes ágeis e projetos de produtos digitais.",
        "workload": "9 horas",
        "event_start": datetime.strptime("2025-11-05T00:00:00.000Z", format),
        "event_end": datetime.strptime("2025-11-07T00:00:00.000Z", format),
        "event_date": datetime.strptime("2025-11-05T00:00:00.000Z", format),
        "issued_at": now,
        "valid_until": add_years(now, 2),
    }

    return result


class CertificateRepository:
    def __init__(self, database: AsyncIOMotorDatabase):
        self.certificates: AsyncIOMotorCollection = database.get_collection(
            "certificates"
        )
        self.auth_collection: AsyncIOMotorCollection = database.get_collection("auth")

    async def create(
        self, user_id: str, certificate_data: CreateCertificate
    ) -> CertificateResponse:
        existingUser = await self.auth_collection.find_one({"_id": ObjectId(user_id)})
        if not existingUser:
            raise Exception("Email não encontrado")

        # Busca informações do evento na collection de events
        existingEvent = mocked_event(
            userId=existingUser.get("_id"),
            participantEmail=existingUser.get("email"),
            participantName=existingUser.get("fullname"),
        )
        if not existingEvent:
            raise Exception("Evento não existe")

        now = datetime.now(timezone.utc)

        certificate_dict = certificate_data.model_dump()
        certificate_dict.update(
            {
                "user_id": str(
                    existingUser.get("_id")
                ),  # Converter ObjectId para string
                "access_key": existingEvent.get(
                    "access_key", str(uuid.uuid4()).upper().replace("-", "")[0:12]
                ),
                "status": existingEvent.get("status", Status.AVALIABLE),
                "participant_name": existingUser.get("fullname"),
                "participant_email": existingUser.get("email"),
                "institution_name": existingEvent.get("institution_name"),
                "event_id": existingEvent.get("_id"),
                "event_name": existingEvent.get("event_name"),
                "description": existingEvent.get("description"),
                "workload": existingEvent.get("workload"),
                "event_start": existingEvent.get("event_start"),
                "event_end": existingEvent.get("event_end"),
                "event_date": existingEvent.get("event_date"),
                "issued_at": now,
                "valid_until": add_years(now, 2),
            }
        )

        # Insere o certificado na collection de certificates
        result = await self.certificates.insert_one(certificate_dict)
        created_certificate = await self.certificates.find_one(
            {"_id": ObjectId(result.inserted_id)}
        )

        if not created_certificate:
            raise Exception("Falha ao criar certificado")

        # Converter ObjectId para string antes de passar para o Pydantic
        created_certificate["_id"] = str(created_certificate["_id"])

        return CertificateResponse(**created_certificate)

    async def get_many_certificates(self, user_id: str) -> list[CertificateResponse]:
        existingUser = await self.auth_collection.find_one({"_id": ObjectId(user_id)})
        if not existingUser:
            raise Exception("Usuário não encontrado")

        cursor = self.certificates.find({"user_id": str(ObjectId(user_id))})
        docs = await cursor.to_list(length=None)

        if not docs or len(docs) < 1:
            raise Exception("Certificados não encontrados")

        for doc in docs:
            doc["_id"] = str(doc["_id"])

        return [CertificateResponse(**doc) for doc in docs]

    async def get_certificate(self, certificate_id: str) -> CertificateResponse:
        existingCertificate = await self.certificates.find_one(
            {"_id": ObjectId(certificate_id)}
        )

        if not existingCertificate:
            raise Exception("Certificado não encontrado.")

        # Converter ObjectId para string antes de passar para o Pydantic
        existingCertificate["_id"] = str(existingCertificate["_id"])

        return CertificateResponse(**existingCertificate)

    # TODO: Create route to validate certificate using validationLink (?)

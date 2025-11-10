import os
from datetime import datetime, timezone

from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

from api_certify.models.certificate_model import (
    CertificateInDb,
    CreateCertificate,
)

ACCESS_KEY = os.getenv('ACCESS_KEY')


def add_years(data: datetime, anos: int) -> datetime:
    """Adiciona um número de anos a uma data, ajustando para anos não bissextos se necessário."""
    try:
        return data.replace(year=data.year + anos)
    except ValueError:
        # Caso especial: 29 de fevereiro → ajusta para 28 de fevereiro
        return data.replace(month=2, day=28, year=data.year + anos)


def mocked_certificate(
    userId: str,
    participantName: str,
    participantEmail: str,
    access_key: str,
    status: str,
) -> dict:
    now = datetime.now(timezone.utc)
    format = '%Y-%m-%dT%H:%M:%S.%fZ'

    result = {
        'user_id': str(userId),
        'access_key': access_key,
        'status': status,
        'participant_name': participantName,
        'participant_email': participantEmail,
        'institution_name': 'Comunidade Frontend Fusion',
        'event_id': '1',
        'event_name': 'Imersão Dev Insights',
        'description': 'Participou da Imersão Dev Insights, realizada nos dias 5, 6 e 7 de novembro, um evento voltado ao aprendizado, conexão e desenvolvimento em gestão de produtos e metodologias ágeis. Durante esta imersão, o(a) participante teve contato com conteúdos ministrados por profissionais experientes, desenvolvendo habilidades essenciais para atuar em ambientes ágeis e projetos de produtos digitais.',
        'workload': '9',
        'event_start': datetime.strptime('2025-11-05T00:00:00.000Z', format),
        'event_end': datetime.strptime('2025-11-07T00:00:00.000Z', format),
        'event_date': datetime.strptime('2025-11-05T00:00:00.000Z', format),
        'issued_at': now,
        'valid_until': add_years(now, 2),
    }

    return result


class CertificateRepository:
    def __init__(self, database: AsyncIOMotorDatabase):
        self.certificate_collection: AsyncIOMotorCollection = (
            database.get_collection('certificates')
        )
        self.auth_collection: AsyncIOMotorCollection = database.get_collection(
            'auth_database'
        )

    async def find_existing_certificate(
        self, user_id: str, certificate_data: CreateCertificate
    ) -> CertificateInDb | None:
        """
        Busca um certificado existente para o usuário e evento específico.
        A chave de unicidade é: user_id + event_id
        """
        existing_certificate = await self.certificate_collection.find_one({
            'user_id': user_id,
            'event_id': certificate_data.event_id,  # Garante que não haja dois certificados do mesmo evento
        })

        if existing_certificate:
            existing_certificate['_id'] = str(existing_certificate['_id'])
            return CertificateInDb(**existing_certificate)
        return None

    async def create(
        self, user_id: str, certificate_data: CreateCertificate
    ) -> CertificateInDb:
        """
        Cria um novo certificado apenas se não existir um para o mesmo usuário e evento
        """

        if certificate_data.access_key != ACCESS_KEY:
            raise Exception('Chave de Acesso Inválido.')

        # Verificação adicional para garantir que não há duplicata
        existing = await self.find_existing_certificate(
            user_id, certificate_data
        )
        if existing:
            return existing

        created_certificate = mocked_certificate(
            userId=user_id,
            participantEmail=certificate_data.email,
            participantName=certificate_data.fullname,
            access_key=certificate_data.access_key,
            status='available',
        )

        result = await self.certificate_collection.insert_one(
            created_certificate
        )
        created_doc = await self.certificate_collection.find_one({
            '_id': result.inserted_id
        })

        if not created_doc:
            raise Exception('Erro ao criar o certificado.')

        existingUser = await self.auth_collection.find_one_and_update(
            {'email': certificate_data.email},
            {'$set': {'status': 'available'}},
            return_document=True,  # Retorna o documento atualizado
        )
        if not existingUser:
            print(
                f'Aviso: Usuário com email {certificate_data.email} não encontrado'
            )

        created_doc['_id'] = str(created_doc['_id'])
        return CertificateInDb(**created_doc)

    async def get_many_certificates(
        self, user_id: str
    ) -> list[CertificateInDb]:
        existingUser = await self.auth_collection.find_one({
            '_id': ObjectId(user_id)
        })
        if not existingUser:
            raise Exception('Usuário não encontrado')

        cursor = self.certificate_collection.find({
            'user_id': str(ObjectId(user_id))
        })
        docs = await cursor.to_list(length=None)

        if not docs or len(docs) < 1:
            raise Exception('Certificados não encontrados')

        for doc in docs:
            doc['_id'] = str(doc['_id'])

        return [CertificateInDb(**doc) for doc in docs]

    async def get_certificate(self, certificate_id: str) -> CertificateInDb:
        existingCertificate = await self.certificate_collection.find_one({
            'user_id': certificate_id
        })

        if not existingCertificate:
            raise Exception('Certificado não encontrado.')

        existingCertificate['_id'] = str(existingCertificate['_id'])
        return CertificateInDb(**existingCertificate)

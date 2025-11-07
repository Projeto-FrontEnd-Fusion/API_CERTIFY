from api_certify.repositories.certificate_repository import CertificateRepository
from api_certify.models.certificate_model import (
    CertificateInDb,
    CreateCertificate,
)
from api_certify.repositories.auth_repository import AuthRepository

class CertificateService:
    def __init__(self, certificate_repository: CertificateRepository, auth_repository: AuthRepository):
        self.certificate_repository = certificate_repository
        self.auth_repository = auth_repository

    async def create_participant_certificate(
        self, user_id: str, certificate_data: CreateCertificate
    ) -> CertificateInDb:

        # Verifica se usuário existe
        isExistingUser = await self.auth_repository.isExistAuth(user_id)
        if not isExistingUser:
            raise Exception('Usuário não existe, certificado não pode ser criado')

        # Busca certificado existente para este usuário e evento
        existing_certificate = await self.certificate_repository.find_existing_certificate(
            user_id, certificate_data
        )

        # Se já existe, retorna o certificado existente
        if existing_certificate:
            return existing_certificate

        # Se não existe, cria um novo
        return await self.certificate_repository.create(user_id, certificate_data)

    async def get_many_certificates(self, user_id: str) -> list[CertificateInDb]:
        certificates = await self.certificate_repository.get_many_certificates(user_id)
        return certificates

    async def get_certificate_by_id(self, certificate_id: str) -> CertificateInDb:
        response = await self.certificate_repository.get_certificate(certificate_id)
        print(certificate_id)
        return response
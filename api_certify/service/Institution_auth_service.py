from api_certify.repositories.Institution_auth_repository import (
    InstitutionAuthRepository,
)
from api_certify.models.auth_institution_model import (
    InstitutionAuth,
    InstitutionAuthResponse,
    InstitutionAuthLogin
)


class InstitutionAuthService:
    def __init__(self, institution_auth_repository: InstitutionAuthRepository):
        self.institution_auth_repository = institution_auth_repository

    async def create_institution(
        self, institution_data: InstitutionAuth
    ) -> InstitutionAuthResponse:
    
        isExistingInstitution = (
            await self.institution_auth_repository.isExistingInstitution(
                institution_data.email
            )
        )

        if isExistingInstitution:
            raise Exception('Email já Cadastrado')
        return await self.institution_auth_repository.create(institution_data)
    
    async def login_institution(
        self, institution_login_data : InstitutionAuthLogin
    ) -> InstitutionAuthResponse:

        isExistingInstitution = (
            await self.institution_auth_repository.isExistingInstitution(
                institution_login_data.email
            )
        )

        if not isExistingInstitution:
           raise Exception("Credenciais inválidas")
        return await self.institution_auth_repository.login(institution_login_data)

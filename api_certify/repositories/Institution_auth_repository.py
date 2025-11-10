from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from api_certify.models.auth_institution_model import (
    InstitutionAuth,
    InstitutionAuthResponse,
    InstitutionAuthLogin
)
from bson import ObjectId
from datetime import datetime, timezone
from api_certify.core.security.hash_manager import HashManager



class InstitutionAuthRepository:
    def __init__(self, database: AsyncIOMotorDatabase):
        self.institution_database: AsyncIOMotorCollection = (
            database.get_collection('auth_institution')
        )
        self.hash: HashManager = HashManager()


    async def isExistingInstitution(self, institution_email: str) -> bool:
        institution = await self.institution_database.find_one({
            'email': institution_email
        })

        return institution is not None
    
    async def create(
        self, institution_data: InstitutionAuth
    ) -> InstitutionAuthResponse:
    
        institution_dict = institution_data.model_dump()
                
        institution_dict.update(
           {
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'password' : self.hash.create_hash(institution_data.password)
           }
        )
        
        result = await self.institution_database.insert_one(institution_dict)

        created_institution = await self.institution_database.find_one({
            '_id': result.inserted_id
        })
        
        if not created_institution:
            raise Exception('Falha ao Criar Instituiçao')
        
        response_data = dict(created_institution)

        response_data['_id'] = str(response_data['_id'])
        del response_data['password']
        return InstitutionAuthResponse(**response_data)

    async def login(
        self, institution_data_login: InstitutionAuthLogin
    ) -> InstitutionAuthResponse:

        institution_in_db = await self.institution_database.find_one(
            {"email" : institution_data_login.email}
        )

        if not institution_in_db:
            raise Exception('Falha ao Econtrar Email')

        isValidPassword = self.hash.verify(
            institution_data_login.password, 
            institution_in_db["password"]
        )

        if not isValidPassword:
            raise Exception("Credenciais inválidas")
        institution_in_db['_id'] = str(institution_in_db['_id'])
        del institution_in_db['password']
        return InstitutionAuthResponse(**institution_in_db)

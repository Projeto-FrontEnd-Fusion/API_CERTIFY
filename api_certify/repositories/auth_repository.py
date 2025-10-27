from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from api_certify.models.auth_model import AuthUser, AuthUserInDb
from datetime import datetime


class AuthRepository:
    def __init__(self, database: AsyncIOMotorDatabase):
        self.collection: AsyncIOMotorCollection = database.auth_database

    async def create(self, auth_data: AuthUser) -> AuthUserInDb:
        isExistEmail = await self.collection.find_one({
            'email': auth_data.email
        })

        if isExistEmail:
            raise Exception('Email já cadastrado')

        auth_dict = auth_data.model_dump()
        auth_dict.update({
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
        })

        result = await self.collection.insert_one(auth_dict)
        created_auth = await self.collection.find_one({
            '_id': result.inserted_id
        })
        if not created_auth:
            raise Exception('Falha ao Criar usuário')
        created_auth['_id'] = str(created_auth['_id'])
        del created_auth['password']
        return AuthUserInDb(**created_auth)

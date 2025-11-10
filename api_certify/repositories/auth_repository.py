from datetime import datetime, timezone

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

from api_certify.core.security.hash_manager import HashManager
from api_certify.models.auth_model import (
    AuthUser,
    AuthUserReponse,
)


class AuthRepository:
    def __init__(self, database: AsyncIOMotorDatabase):
        self.collection: AsyncIOMotorCollection = database.auth_database

    async def isExistAuth(self, user_id: str) -> bool:
        auth_in_db = await self.collection.find_one({'_id': ObjectId(user_id)})
        return auth_in_db is not None

    async def create(self, auth_data: AuthUser) -> AuthUserReponse:
        isExistEmail = await self.collection.find_one({
            'email': auth_data.email
        })

        if isExistEmail:
            raise Exception('Email já cadastrado')

        auth_dict = auth_data.model_dump()
        hash = HashManager()
        auth_dict.update({
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'status': 'pending',
            'password': hash.create_hash(auth_data.password),
        })

        result = await self.collection.insert_one(auth_dict)
        created_auth = await self.collection.find_one({
            '_id': result.inserted_id
        })
        if not created_auth:
            raise Exception('Falha ao Criar usuário')
        created_auth['_id'] = str(created_auth['_id'])
        del created_auth['password']
        return AuthUserReponse(**created_auth)

    async def login(self, auth_data: AuthUser) -> AuthUserReponse:
        auth_in_db = await self.collection.find_one({'email': auth_data.email})
        if not auth_in_db:
            raise Exception('Credenciais Inválidas')

        hash = HashManager()
        isValidPassword = hash.verify(
            auth_data.password, auth_in_db['password']
        )

        if not isValidPassword:
            raise Exception('Credenciais Inválidas')

        del auth_in_db['password']
        auth_in_db['_id'] = str(auth_in_db['_id'])
        print(auth_in_db)
        return AuthUserReponse(**auth_in_db)

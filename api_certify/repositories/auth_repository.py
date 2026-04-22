from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from api_certify.models.auth_model import AuthUser, AuthUserReponse, AuthUserLogin, UpdateUserSchema
from datetime import datetime, timezone
from api_certify.core.security import HashManager
from bson import ObjectId


class AuthRepository:

    def __init__(self, database: AsyncIOMotorDatabase):
        self.collection: AsyncIOMotorCollection = database.auth_database

    async def isExistAuth(self, user_id: str) -> bool:
        """
        Verifica se o usuário existe no banco
        """
        auth_in_db = await self.collection.find_one({"_id": ObjectId(user_id)})
        return auth_in_db is not None

    async def create(self, auth_data: AuthUser) -> AuthUserReponse:
        """
        Cria um novo usuário
        """

        is_exist_email = await self.collection.find_one({"email": auth_data.email})

        if is_exist_email:
            raise Exception("Email já cadastrado")

        auth_dict = auth_data.model_dump()

        auth_dict.update(
            {
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "status": "pending",
                "password": HashManager.hash_password(auth_data.password),
            }
        )

        result = await self.collection.insert_one(auth_dict)

        created_auth = await self.collection.find_one({"_id": result.inserted_id})

        if not created_auth:
            raise Exception("Falha ao criar usuário")

        # converte ObjectId para string
        created_auth["_id"] = str(created_auth["_id"])

        # remove senha da resposta
        del created_auth["password"]

        return AuthUserReponse(**created_auth)

    async def login(self, auth_data: AuthUserLogin) -> AuthUserReponse:
        """
        Realiza login do usuário
        """

        auth_in_db = await self.collection.find_one({"email": auth_data.email})

        if not auth_in_db:
            raise Exception("Credenciais inválidas")

        is_valid_password = HashManager.verify_password(
            auth_data.password,
            auth_in_db["password"],
        )

        if not is_valid_password:
            raise Exception("Credenciais inválidas")

        # remove senha
        del auth_in_db["password"]

        # converte ObjectId para string
        auth_in_db["_id"] = str(auth_in_db["_id"])

        return AuthUserReponse(**auth_in_db)

    async def update(self, user_id: str, update_data: UpdateUserSchema) -> AuthUserReponse:
        fields = update_data.model_dump(exclude_none=True)

        if not fields:
            raise Exception("Nenhum campo para atualizar")

        if "email" in fields:
            existing = await self.collection.find_one({
                "email": fields["email"],
                "_id": {"$ne": ObjectId(user_id)},
            })
            if existing:
                raise Exception("Email já cadastrado")

        fields["updated_at"] = datetime.now(timezone.utc)

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": fields},
            return_document=True,
        )

        if not result:
            raise Exception("Usuário não encontrado")

        result["_id"] = str(result["_id"])
        del result["password"]

        return AuthUserReponse(**result)

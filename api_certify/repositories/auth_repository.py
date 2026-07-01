from datetime import datetime, timezone

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

from api_certify.core.security import HashManager
from api_certify.models.auth_model import (
    AuthUser,
    AuthUserLogin,
    AuthUserReponse,
    CompanyResponse,
    CompanyUser,
    Role,
    UpdateUserSchema,
)
from api_certify.schemas.company_schema import validar_cnpj


class AuthRepository:

    def __init__(self, database: AsyncIOMotorDatabase):
        self.collection: AsyncIOMotorCollection = database.auth_database

    async def isExistAuth(self, user_id: str) -> bool:
        """
        Verifica se o usuário existe no banco
        """
        auth_in_db = await self.collection.find_one({"_id": ObjectId(user_id)})
        return auth_in_db is not None

    async def find_by_email(self, email: str) -> dict | None:
        """
        Busca um usuário pelo e-mail para emissão de certificados em lote.
        """
        normalized_email = email.strip().lower()
        user = await self.collection.find_one({"email": normalized_email})

        if user:
            user["_id"] = str(user["_id"])

        return user

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

    async def get_user_by_id(self, user_id: str) -> AuthUserReponse:
        """
        Busca usuário pelo ID
        """

        auth_in_db = await self.collection.find_one({"_id": ObjectId(user_id)})

        if not auth_in_db:
            raise Exception("Usuário não encontrado")

        # remove senha
        del auth_in_db["password"]

        # converte ObjectId para string
        auth_in_db["_id"] = str(auth_in_db["_id"])

        return AuthUserReponse(**auth_in_db)

    async def update(
        self, user_id: str, update_data: UpdateUserSchema
    ) -> AuthUserReponse:
        fields = update_data.model_dump(exclude_none=True)

        if not fields:
            raise Exception("Nenhum campo para atualizar")

        if "email" in fields:
            existing = await self.collection.find_one(
                {
                    "email": fields["email"],
                    "_id": {"$ne": ObjectId(user_id)},
                }
            )
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

    async def create_company(self, company_data: CompanyUser) -> CompanyResponse:
        """
        Cria uma nova empresa com validação de CNPJ e checagem de duplicatas
        """

        # normalizar e validar cnpj
        try:
            cnpj_normalized = validar_cnpj(company_data.cnpj)
        except ValueError:
            raise Exception("CNPJ inválido")

        # checar duplicidade de CNPJ
        existing_cnpj = await self.collection.find_one({"cnpj": cnpj_normalized})

        if existing_cnpj:
            raise Exception("CNPJ já cadastrado")

        # checar duplicidade de email
        existing_email = await self.collection.find_one({"email": company_data.email})

        if existing_email:
            raise Exception("Email já cadastrado")

        company_dict = company_data.model_dump()

        company_dict.update(
            {
                "cnpj": cnpj_normalized,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "status": "pending",
                "password": HashManager.hash_password(company_data.password),
                "role": (
                    Role.EMPRESA.value if hasattr(Role, "EMPRESA") else Role.EMPRESA
                ),
            }
        )

        result = await self.collection.insert_one(company_dict)

        created = await self.collection.find_one({"_id": result.inserted_id})

        if not created:
            raise Exception("Falha ao criar empresa")

        created["_id"] = str(created["_id"])
        del created["password"]

        return CompanyResponse(**created)

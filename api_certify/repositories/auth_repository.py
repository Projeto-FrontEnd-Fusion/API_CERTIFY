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
        self.reset_codes_collection: AsyncIOMotorCollection = database.get_collection(
            'password_reset_codes'
        )

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

    async def get_user_by_email(self, email: str):
        auth_in_db = await self.collection.find_one({"email": email})

        if not auth_in_db:
            return None

        auth_in_db["_id"] = str(auth_in_db["_id"])
        del auth_in_db["password"]

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

    async def store_password_reset_code(
        self,
        user_id: str,
        code_hash: str,
        expires_at: datetime,
    ) -> dict:
        now = datetime.now(timezone.utc)

        await self.reset_codes_collection.update_many(
            {"user_id": user_id, "used": False, "expires_at": {"$gt": now}},
            {"$set": {"used": True, "invalidated_at": now, "reason": "replaced"}},
        )

        doc = {
            "user_id": user_id,
            "code_hash": code_hash,
            "expires_at": expires_at,
            "created_at": now,
            "attempts": 0,
            "used": False,
        }

        await self.reset_codes_collection.insert_one(doc)
        return doc

    async def verify_password_reset_code(self, user_id: str, code: str) -> dict:
        now = datetime.now(timezone.utc)

        reset_code = await self.reset_codes_collection.find_one(
            {"user_id": user_id, "used": False, "expires_at": {"$gt": now}},
            sort=[("created_at", -1)],
        )

        if not reset_code:
            return {"success": False, "message": "Código inválido ou expirado"}

        if reset_code["attempts"] >= 3:
            await self.reset_codes_collection.update_one(
                {"_id": reset_code["_id"]},
                {"$set": {"used": True, "invalidated_at": now, "reason": "max_attempts"}},
            )
            return {"success": False, "message": "Máximo de tentativas atingido"}

        is_valid = HashManager.verify_password(code, reset_code["code_hash"])

        if not is_valid:
            next_attempts = reset_code["attempts"] + 1
            await self.reset_codes_collection.update_one(
                {"_id": reset_code["_id"]},
                {"$set": {"attempts": next_attempts}},
            )

            if next_attempts >= 3:
                await self.reset_codes_collection.update_one(
                    {"_id": reset_code["_id"]},
                    {"$set": {"used": True, "invalidated_at": now, "reason": "max_attempts"}},
                )

            return {"success": False, "message": "Código inválido"}

        return {"success": True, "message": "Código verificado com sucesso"}

    async def reset_password_with_code(
        self,
        user_id: str,
        code: str,
        new_password: str,
    ) -> dict:
        now = datetime.now(timezone.utc)

        reset_code = await self.reset_codes_collection.find_one(
            {"user_id": user_id, "used": False, "expires_at": {"$gt": now}},
            sort=[("created_at", -1)],
        )

        if not reset_code:
            return {"success": False, "message": "Código inválido ou expirado"}

        if reset_code["attempts"] >= 3:
            await self.reset_codes_collection.update_one(
                {"_id": reset_code["_id"]},
                {"$set": {"used": True, "invalidated_at": now, "reason": "max_attempts"}},
            )
            return {"success": False, "message": "Máximo de tentativas atingido"}

        is_valid = HashManager.verify_password(code, reset_code["code_hash"])

        if not is_valid:
            next_attempts = reset_code["attempts"] + 1
            await self.reset_codes_collection.update_one(
                {"_id": reset_code["_id"]},
                {"$set": {"attempts": next_attempts}},
            )

            if next_attempts >= 3:
                await self.reset_codes_collection.update_one(
                    {"_id": reset_code["_id"]},
                    {"$set": {"used": True, "invalidated_at": now, "reason": "max_attempts"}},
                )

            return {"success": False, "message": "Código inválido"}

        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"password": HashManager.hash_password(new_password), "updated_at": now}},
        )

        await self.reset_codes_collection.update_one(
            {"_id": reset_code["_id"]},
            {"$set": {"used": True, "invalidated_at": now, "reason": "reset"}},
        )

        return {"success": True, "message": "Senha redefinida com sucesso"}

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

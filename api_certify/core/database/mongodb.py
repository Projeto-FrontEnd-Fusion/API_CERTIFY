from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()
DB_NAME = os.getenv('DB_NAME')
DB_URL = os.getenv('DB_URL')

if not DB_NAME or not DB_URL:
    raise RuntimeError(
        'As variáveis de ambiente DB_NAME e DB_URL devem estar definidas.'
    )


class MongoDBConnection:
    def __init__(self):
        self._client: Optional[AsyncIOMotorClient] = None
        self._database: Optional[AsyncIOMotorDatabase] = None

    async def connect(self, db_url: str, db_name: str) -> None:
        try:
            self._client = AsyncIOMotorClient(
                db_url,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
            )
            # Ping para validar conexão real
            await self._client.admin.command('ping')
            self._database = self._client[db_name]
        except Exception as e:
            self._client = None
            self._database = None
            raise RuntimeError(
                'Falha ao conectar ao banco de dados. '
                'Verifique se o servidor está ativo e as credenciais estão corretas.'
            )

    async def disconnect(self) -> None:
        if self._client:
            self._client.close()
            self._client = None
            self._database = None

    async def get_database(self) -> AsyncIOMotorDatabase:
        if self._database is None:
            raise RuntimeError(
                'Aplicação não conectada ao MongoDB. '
                'Verifique se o banco de dados está ativo.'
            )
        return self._database

    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._database is not None


db_mongo = MongoDBConnection()


async def mongodb_connect() -> None:
    await db_mongo.connect(DB_URL, DB_NAME)


async def mongodb_disconnect() -> None:
    await db_mongo.disconnect()


async def get_db() -> AsyncIOMotorDatabase:
    return await db_mongo.get_database()

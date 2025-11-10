import os
from typing import Optional

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

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
            self._client = AsyncIOMotorClient(db_url)
            self._database = self._client[db_name]
        except Exception as e:
            raise RuntimeError(f'Falha ao conectar ao MongoDB: {e}')

    async def disconnect(self) -> None:
        if self._client:
            self._client.close()
            self._client = None
            self._database = None

    async def get_database(self) -> AsyncIOMotorDatabase:
        if self._database is None:
            raise RuntimeError('Aplicação não conectada ao MongoDB Atlas')
        return self._database


db_mongo = MongoDBConnection()


async def mongodb_connect() -> None:
    await db_mongo.connect(DB_URL, DB_NAME)


async def mongodb_disconnect() -> None:
    await db_mongo.disconnect()


async def get_db() -> AsyncIOMotorDatabase:
    return await db_mongo.get_database()

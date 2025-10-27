from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional


class MongoDBConnection:
    def __init__(self):
        self.clienteMongo: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None

    async def connect(self, DB_URI: str, DB_NAME: str) -> None:
        if not DB_URI or not DB_NAME:
            raise RuntimeError(
                'A string de Conexão com o MongoDb é obrigatória'
            )

        try:
            self.clienteMongo = AsyncIOMotorClient(DB_URI)
            self.database = self.clienteMongo[DB_NAME]

        except Exception:
            raise RuntimeError('Falha ao Obter conexão com o mongodb Atlas')

    async def disconnect(self) -> None:
        if self.clienteMongo:
            self.clienteMongo.close()
            self.clienteMongo = None
            self.database = None

    async def get_database(self) -> AsyncIOMotorDatabase:
        if self.database is None:
            raise RuntimeError('Aplicação não conectada ao MongoDB Atlas')
        return self.database

db_mongo = MongoDBConnection()

async def mongodb_connect(DB_URI: str, DB_NAME: str) -> None:
  await db_mongo.connect()

async def mongodb_disconnect() -> None:
  await db_mongo.disconnect()

def get_db() -> AsyncIOMotorDatabase:
  return db_mongo.get_database()

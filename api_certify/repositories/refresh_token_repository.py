import hashlib
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class RefreshTokenRepository:

    def __init__(self, database: AsyncIOMotorDatabase):
        self.collection: AsyncIOMotorCollection = database.get_collection("refresh_tokens")

    async def create(self, user_id: str, token: str, expires_at: datetime) -> dict:
        token_hash = _hash_token(token)

        doc = {
            "user_id": user_id,
            "token_hash": token_hash,
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc),
            "revoked": False,
        }

        await self.collection.insert_one(doc)

        # Limitar a 5 tokens ativos por usuário
        active_tokens = await self.collection.count_documents({
            "user_id": user_id,
            "revoked": False,
        })

        if active_tokens > 5:
            oldest = self.collection.find({
                "user_id": user_id,
                "revoked": False,
            }).sort("created_at", 1).limit(active_tokens - 5)

            async for old_token in oldest:
                await self.collection.update_one(
                    {"_id": old_token["_id"]},
                    {"$set": {"revoked": True}},
                )

        return doc

    async def find_valid_token(self, token: str) -> dict | None:
        token_hash = _hash_token(token)

        doc = await self.collection.find_one({
            "token_hash": token_hash,
            "revoked": False,
        })

        if not doc:
            return None

        # Verificar expiração
        if doc["expires_at"] < datetime.now(timezone.utc):
            await self.revoke(token)
            return None

        return doc

    async def revoke(self, token: str) -> bool:
        token_hash = _hash_token(token)

        result = await self.collection.update_one(
            {"token_hash": token_hash},
            {"$set": {"revoked": True}},
        )
        return result.modified_count > 0

    async def revoke_all_for_user(self, user_id: str) -> int:
        result = await self.collection.update_many(
            {"user_id": user_id, "revoked": False},
            {"$set": {"revoked": True}},
        )
        return result.modified_count

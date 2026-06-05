from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection

from api_certify.models.event_model import CreateEvent, EventInDb


class EventRepository:

    def __init__(self, database: AsyncIOMotorDatabase):
        self.collection: AsyncIOMotorCollection = database.get_collection("events")

    async def create(self, event_data: CreateEvent) -> EventInDb:
        event_dict = event_data.model_dump()
        event_dict["created_at"] = datetime.now(timezone.utc)

        result = await self.collection.insert_one(event_dict)

        created = await self.collection.find_one({"_id": result.inserted_id})

        if not created:
            raise Exception("Falha ao criar evento")

        created["_id"] = str(created["_id"])

        return EventInDb(**created)

    async def find_by_id(self, event_id: str) -> EventInDb | None:
        try:
            oid = ObjectId(event_id)
        except (InvalidId, Exception):
            return None

        doc = await self.collection.find_one({"_id": oid})

        if not doc:
            return None

        doc["_id"] = str(doc["_id"])

        return EventInDb(**doc)

    async def exists(self, event_id: str) -> bool:
        try:
            oid = ObjectId(event_id)
        except (InvalidId, Exception):
            return False

        doc = await self.collection.find_one({"_id": oid})
        return doc is not None

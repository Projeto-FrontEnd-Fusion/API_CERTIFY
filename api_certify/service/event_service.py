from api_certify.repositories.event_repository import EventRepository
from api_certify.models.event_model import CreateEvent, EventInDb, UpdateEventSchema


class EventService:

    def __init__(self, event_repository: EventRepository):
        self.event_repository = event_repository

    async def create_event(self, event_data: CreateEvent) -> EventInDb:
        return await self.event_repository.create(event_data)

    async def get_event_by_id(self, event_id: str) -> EventInDb | None:
        return await self.event_repository.find_by_id(event_id)

    async def update_event(self, event_id: str, update_data: UpdateEventSchema) -> EventInDb | None:
        return await self.event_repository.update(event_id, update_data)
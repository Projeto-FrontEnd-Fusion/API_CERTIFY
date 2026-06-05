from api_certify.repositories.event_repository import EventRepository
from api_certify.models.event_model import CreateEvent, EventInDb
from fastapi import HTTPException, status


class EventService:

    def __init__(self, event_repository: EventRepository):
        self.event_repository = event_repository

    async def create_event(self, event_data: CreateEvent) -> EventInDb:
        return await self.event_repository.create(event_data)

    async def get_event_by_id(self, event_id: str) -> EventInDb | None:
        return await self.event_repository.find_by_id(event_id)

    async def delete_event(self, event_id: str) -> None:
        # Verificar se evento existe
        event = await self.event_repository.find_by_id(event_id)

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento não encontrado",
            )

        # Verificar se tem certificados emitidos
        has_certs = await self.event_repository.has_certificates(event_id)

        if has_certs:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Não é possível excluir um evento que já possui certificados emitidos.",
            )

        await self.event_repository.delete(event_id)

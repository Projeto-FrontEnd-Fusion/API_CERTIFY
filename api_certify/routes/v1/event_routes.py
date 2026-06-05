from fastapi import APIRouter, Depends, HTTPException

from api_certify.dependencies import get_event_service, get_current_user
from api_certify.models.event_model import CreateEvent
from api_certify.schemas.responses import SucessResponse
from api_certify.service.event_service import EventService

event_routes = APIRouter(prefix="/events", tags=["Events"])


@event_routes.post(
    "",
    response_model=SucessResponse,
    status_code=201,
)
async def create_event(
    payload: CreateEvent,
    service: EventService = Depends(get_event_service),
    current_user: dict = Depends(get_current_user),
):
    try:
        event = await service.create_event(payload)

        return SucessResponse(
            success=True,
            message="Evento criado com sucesso.",
            data={"event": event},
        )

    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err))


@event_routes.get(
    "/{event_id}",
    response_model=SucessResponse,
    status_code=200,
)
async def get_event(
    event_id: str,
    service: EventService = Depends(get_event_service),
):
    event = await service.get_event_by_id(event_id)

    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    return SucessResponse(
        success=True,
        message="Evento obtido com sucesso.",
        data={"event": event},
    )

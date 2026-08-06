from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from api_certify.models.event_model import EventInDb, UpdateEventSchema
from api_certify.service.event_service import EventService


@pytest.mark.asyncio
async def test_update_event_delegates_to_repository_and_returns_updated_event():
    repository = AsyncMock()
    repository.update.return_value = EventInDb(
        _id="event-123",
        name="Evento Atualizado",
        institution="Instituição",
        workload=12,
        description="Descrição atualizada",
        start_date=datetime(2025, 11, 5, 0, 0),
        end_date=datetime(2025, 11, 7, 0, 0),
    )

    service = EventService(repository)
    payload = UpdateEventSchema(name="Evento Atualizado", workload=12)

    result = await service.update_event("event-123", payload)

    repository.update.assert_awaited_once_with("event-123", payload)
    assert result is not None
    assert result.name == "Evento Atualizado"
    assert result.workload == 12

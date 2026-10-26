from fastapi import APIRouter, Depends, Query

from api_certify.core.database.mongodb import db_mongo
from api_certify.dependencies import require_role
from api_certify.models.notification_model import (
    NotificationPageResponse,
    NotificationReadResponse,
    NotificationsReadResponse,
)
from api_certify.service.notification_service import NotificationService

notification_routes = APIRouter(
    prefix='/notifications',
    tags=['Notifications'],
)


async def get_notification_service():
    return NotificationService(await db_mongo.get_database())


@notification_routes.get('', response_model=NotificationPageResponse)
async def list_notifications(
    page: int = Query(1, ge=1),
    limit: int = Query(5, ge=1, le=100),
    user: dict = Depends(require_role('empresa')),
    service: NotificationService = Depends(get_notification_service),
):
    return NotificationPageResponse(
        data=await service.list(user['sub'], page, limit),
    )


@notification_routes.patch(
    '/read-all', response_model=NotificationsReadResponse
)
async def read_all_notifications(
    user: dict = Depends(require_role('empresa')),
    service: NotificationService = Depends(get_notification_service),
):
    return NotificationsReadResponse(
        data={'updated': await service.mark_all_read(user['sub'])},
    )


@notification_routes.patch(
    '/{notification_id}/read', response_model=NotificationReadResponse
)
async def read_notification(
    notification_id: str,
    user: dict = Depends(require_role('empresa')),
    service: NotificationService = Depends(get_notification_service),
):
    return NotificationReadResponse(
        data={
            'notification': await service.mark_read(
                user['sub'], notification_id
            )
        },
    )

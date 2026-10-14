from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, field_validator


class Notification(BaseModel):
    id: str
    type: Literal['certificate']
    severity: Literal['info', 'warning']
    title: str
    description: str
    created_at: datetime
    read: bool
    href: str

    @field_validator('created_at')
    @classmethod
    def utc_date(cls, value):
        # Motor's default BSON decoding returns naive UTC datetimes.
        return (
            value.replace(tzinfo=timezone.utc)
            if value.tzinfo is None
            else value.astimezone(timezone.utc)
        )


class NotificationPage(BaseModel):
    items: list[Notification]
    total: int
    unread_count: int
    page: int
    total_pages: int


class NotificationPageResponse(BaseModel):
    success: bool = True
    message: str = 'Notificações obtidas com sucesso.'
    data: NotificationPage


class NotificationReadData(BaseModel):
    notification: Notification


class NotificationReadResponse(BaseModel):
    success: bool = True
    message: str = 'Notificação marcada como lida.'
    data: NotificationReadData


class NotificationsReadData(BaseModel):
    updated: int


class NotificationsReadResponse(BaseModel):
    success: bool = True
    message: str = 'Notificações marcadas como lidas.'
    data: NotificationsReadData

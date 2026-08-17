from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.notification import NotificationType


class NotificationRead(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    type: str
    status: str
    link: str | None
    metadata_json: dict[str, Any] | None
    read_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationPageRead(BaseModel):
    items: list[NotificationRead]
    page: int
    page_size: int
    total_items: int
    total_pages: int


class NotificationUnreadCountRead(BaseModel):
    unread_count: int


class NotificationBulkActionRead(BaseModel):
    affected: int


class NotificationStatusRead(BaseModel):
    notification_id: int
    status: str
    read_at: datetime | None


class NotificationBroadcastRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1)
    link: str | None = Field(default=None, max_length=255)
    type: NotificationType = NotificationType.admin_announcement
    recipient_roles: list[str] | None = Field(default=None)


class NotificationBroadcastRead(BaseModel):
    type: str
    title: str
    message: str
    link: str | None
    recipients_count: int

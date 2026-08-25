from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_user_id: Optional[int] = None
    actor_email: Optional[str] = None
    action: str
    resource: str
    resource_id: Optional[str] = None
    before: Optional[dict[str, Any]] = None
    after: Optional[dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime


class AuditLogPageRead(BaseModel):
    items: List[AuditLogRead]
    page: int
    page_size: int
    total_items: int
    total_pages: int


class LoginHistoryEntryRead(BaseModel):
    """A single login attempt as exposed to its owner (WIQ-V1-019).

    ``outcome`` is the public value ("success" / "failure"), derived from the
    internal audit action ("login_success" / "login_failure") so records can be
    validated straight from ``AuditLog`` ORM rows. Internal audit metadata
    (action, resource, resource_id, before/after snapshots) is deliberately not
    part of the login-history surface.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    outcome: Literal["success", "failure"] = Field(
        validation_alias=AliasChoices("outcome", "action"),
    )
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    @field_validator("outcome", mode="before")
    @classmethod
    def _map_action_to_outcome(cls, value: object) -> object:
        if isinstance(value, str) and value.startswith("login_"):
            return value.removeprefix("login_")
        return value


class AdminLoginHistoryEntryRead(LoginHistoryEntryRead):
    actor_user_id: Optional[int] = None
    actor_email: Optional[str] = None


class LoginHistoryPageRead(BaseModel):
    items: List[LoginHistoryEntryRead]
    page: int
    page_size: int
    total_items: int
    total_pages: int


class AdminLoginHistoryPageRead(BaseModel):
    items: List[AdminLoginHistoryEntryRead]
    page: int
    page_size: int
    total_items: int
    total_pages: int

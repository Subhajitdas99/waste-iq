from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AuditLog(Base):
    """Append-only audit trail for security-sensitive and administrative actions.

    Records are created transactionally with the action they describe and are
    never updated or deleted through application code.
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    resource: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    resource_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    before: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    actor = relationship("User")

    @property
    def actor_email(self) -> str | None:
        return self.actor.email if self.actor is not None else None

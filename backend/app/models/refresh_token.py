from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class RefreshToken(Base):
    """Server-side refresh-token session (WIQ-V1-013).

    Only the SHA-256 digest of the opaque token is stored; the raw token is
    handed to the client exactly once at issuance and never persisted.

    Rotation keeps the same ``family_id``; ``replaced_by`` links each token to
    the one that superseded it. Presenting an already-rotated token is treated
    as reuse and revokes the entire family.
    """

    __tablename__ = "refresh_tokens"
    __table_args__ = (
        # Accelerates family-wide revocation on reuse detection.
        Index("ix_refresh_tokens_family_id", "family_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    family_id: Mapped[str] = mapped_column(String(36), nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    replaced_by: Mapped[int | None] = mapped_column(
        ForeignKey("refresh_tokens.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )

    user = relationship("User")

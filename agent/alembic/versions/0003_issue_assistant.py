"""Issue assistant schema

Revision ID: 0003_issue_assistant
Revises: 0002_review
Create Date: 2026-08-06

Adds: agent_runs.assistant, agent_runs.outcome (Phase 3 Issue Assistant run ledger).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_issue_assistant"
down_revision: Union[str, None] = "0002_review"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("agent_runs", sa.Column("assistant", sa.String(length=64), nullable=True))
    op.add_column("agent_runs", sa.Column("outcome", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("agent_runs", "outcome")
    op.drop_column("agent_runs", "assistant")

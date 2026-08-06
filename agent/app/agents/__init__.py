"""Assistants package — one module per assistant (Phase 3+: Issue Assistant)."""

from app.agents.base import AssistantRegistry
from app.agents.issue_agent import IssueAssistant, IssueTriage, format_comment

__all__ = ["AssistantRegistry", "IssueAssistant", "IssueTriage", "format_comment"]

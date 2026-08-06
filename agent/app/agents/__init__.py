"""Assistants package — one module per assistant (Phase 3+: Issue Assistant, Doc Assistant)."""

from app.agents.base import AssistantRegistry
from app.agents.doc_agent import DocAssistant, DocProposal, format_proposal_comment
from app.agents.issue_agent import IssueAssistant, IssueTriage, format_comment

__all__ = [
    "AssistantRegistry",
    "DocAssistant",
    "DocProposal",
    "IssueAssistant",
    "IssueTriage",
    "format_comment",
    "format_proposal_comment",
]

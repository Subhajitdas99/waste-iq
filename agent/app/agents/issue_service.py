"""Application service for the Issue Assistant.

Dispatches webhook-triggered triage of new issues, records runs in the
state DB, and — only when explicitly enabled — posts an idempotent
propose-only comment. Never touches labels, milestones, or issue state.
"""

from __future__ import annotations

import json
import logging

from app.agents.issue_agent import (
    _COMMENT_ANCHOR,
    IssueAssistant,
    format_comment,
)
from app.coordinator.event_handler import EventEnvelope
from app.core.config import settings
from app.db.models import AgentRun, AuditLogEntry
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

_ISSUE_ACTIONS = {"opened", "reopened"}


class IssueService:
    def __init__(
        self,
        container=None,
        session_factory=None,
        rest_client=None,
        assistant: IssueAssistant | None = None,
    ) -> None:
        self._container = container
        self._session_factory = session_factory or SessionLocal
        self._injected_rest = rest_client
        self._assistant = assistant or IssueAssistant(container)
        self._token: str | None = None

    @property
    def container(self):
        if self._container is None:
            from app.api.dependencies import get_container

            self._container = get_container()
        return self._container

    # ------------------------------------------------------------------
    async def handle_event(self, envelope: EventEnvelope) -> dict | None:
        """Dispatch a webhook event to issue triage, if it is one."""
        if not settings.agent_issue_enabled or not settings.agent_issue_auto_run:
            return None
        if envelope.event_type != "issues" or envelope.event_action not in _ISSUE_ACTIONS:
            return None
        issue = envelope.payload.get("issue") or {}
        repo_full_name = envelope.payload.get("repository", {}).get("full_name")
        number = issue.get("number")
        if not repo_full_name or not number:
            return None
        return await self._run(repo_full_name, issue, envelope)

    async def _run(self, repo_full_name: str, issue: dict, envelope: EventEnvelope) -> dict:
        owner, _, repo_name = repo_full_name.partition("/")
        rest = self._rest_client(owner, repo_name)
        open_issues: list[dict] | None = None
        repo_labels: list[str] | None = None
        if rest is not None:
            try:
                open_issues = await rest.list_open_issues(per_page=30)
                labels = await rest.list_labels(per_page=100)
                repo_labels = [label.get("name") for label in labels]
            except Exception:  # noqa: BLE001 - network trouble degrades to offline triage
                logger.warning(
                    "issue triage context fetch failed repo=%s issue=%s",
                    repo_full_name,
                    issue.get("number"),
                    exc_info=True,
                )

        triage = self._assistant.analyze(issue, open_issues=open_issues, repo_labels=repo_labels)

        comment_posted = False
        comment_skipped = False
        if settings.agent_issue_comments_enabled and rest is not None:
            try:
                comment_posted, comment_skipped = await self._post_comment(rest, triage)
            except Exception:  # noqa: BLE001 - a comment failure must not fail the event
                logger.warning(
                    "issue triage comment failed repo=%s issue=%s",
                    repo_full_name,
                    triage.issue_number,
                    exc_info=True,
                )

        outcome = self._record_run(
            envelope, triage, repo_full_name, comment_posted, comment_skipped
        )
        logger.info(
            "issue triage done repo=%s issue=%s labels=%s priority=%s duplicates=%d",
            repo_full_name,
            triage.issue_number,
            triage.suggested_labels,
            triage.priority,
            len(triage.duplicate_of),
        )
        return outcome

    async def _post_comment(self, rest, triage) -> tuple[bool, bool]:
        """Post the propose-only comment, anchored and idempotent."""
        existing = await rest.list_issue_comments(triage.issue_number, per_page=100)
        if any(_COMMENT_ANCHOR in (comment.get("body") or "") for comment in existing):
            return False, True
        await rest.create_issue_comment(triage.issue_number, format_comment(triage))
        return True, False

    # ------------------------------------------------------------------
    def _rest_client(self, owner: str, repo: str):
        if self._injected_rest is not None:
            return self._injected_rest
        if not settings.github_configured:
            return None
        token = self._installation_token()
        if token is None:
            return None

        async def _token() -> str:
            return token

        from app.clients.github_rest import GitHubRESTClient

        return GitHubRESTClient(
            owner,
            repo,
            token_provider=_token,
            base_url=settings.agent_github_api_base_url,
        )

    def _installation_token(self) -> str | None:
        if self._token:
            return self._token
        from app.clients.github_app import request_installation_token_sync

        try:
            self._token = request_installation_token_sync(
                settings.agent_github_app_id,
                settings.github_private_key or "",
                settings.agent_github_installation_id,
            )
        except Exception:  # noqa: BLE001 - degrade to offline triage
            logger.warning("issue assistant: installation token unavailable", exc_info=True)
            return None
        return self._token

    def _record_run(
        self,
        envelope: EventEnvelope,
        triage,
        repo_full_name: str,
        comment_posted: bool,
        comment_skipped: bool,
    ) -> dict:
        outcome = {
            "repo": repo_full_name,
            "issue_number": triage.issue_number,
            "labels": triage.suggested_labels,
            "priority": triage.priority,
            "milestone": triage.milestone,
            "duplicates": triage.duplicate_of,
            "evidence_count": len(triage.evidence),
            "comment_posted": comment_posted,
            "comment_skipped": comment_skipped,
        }
        db = self._session_factory()
        try:
            run = db.query(AgentRun).filter(AgentRun.delivery_id == envelope.delivery_id).first()
            if run is None:
                run = AgentRun(
                    delivery_id=envelope.delivery_id,
                    event_type=envelope.event_type,
                    event_action=envelope.event_action,
                    status="processed",
                )
                db.add(run)
            run.assistant = "issue"
            run.status = "processed"
            run.outcome = json.dumps(outcome)
            db.add(
                AuditLogEntry(
                    delivery_id=envelope.delivery_id,
                    actor="waste-iq-agent",
                    action="issue.triage",
                    detail=json.dumps(outcome),
                )
            )
            db.commit()
        finally:
            db.close()
        return outcome

"""Application service for the Documentation Agent (Phase 4).

Two flows, both gated:

1. **Proposal** — a merged PR triggers a propose-only anchored comment with a
   changelog entry and doc-drift suggestions (``AGENT_DOCS_AUTO_RUN`` +
   ``AGENT_DOCS_COMMENTS_ENABLED``).
2. **Patch PR** — a human replies ``/agent docs apply`` on the PR that carries
   the agent's proposal anchor; a patch PR is opened from an ``agent/docs-*``
   branch with the changelog insertion (``AGENT_DOCS_PATCH_PR_ENABLED``).
   Without the proposal anchor, the command is refused: the agent only writes
   where it previously proposed.

The patch-PR write path is the agent's only repository write and is scoped to
``agent/docs-*`` branches, per the capabilities matrix (§5.3).
"""

from __future__ import annotations

import base64
import json
import logging
import re

from app.agents.doc_agent import (
    _APPLY_COMMAND,
    _COMMENT_ANCHOR,
    DocAssistant,
    DocProposal,
    apply_changelog_insertion,
    build_changelog_entry,
    format_proposal_comment,
    patch_branch_name,
)
from app.coordinator.event_handler import EventEnvelope
from app.core.config import settings
from app.db.models import AgentRun, AuditLogEntry
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

_MERGED_ACTIONS = {"closed"}
_APPLY_ACTIONS = {"created"}
_PR_URL_RE = re.compile(r"/(?:pull|issues)/(\d+)/?$")


class DocService:
    def __init__(
        self,
        container=None,
        session_factory=None,
        rest_client=None,
        assistant: DocAssistant | None = None,
    ) -> None:
        self._container = container
        self._session_factory = session_factory or SessionLocal
        self._injected_rest = rest_client
        self._assistant = assistant or DocAssistant()
        self._token: str | None = None

    # ------------------------------------------------------------------
    async def handle_event(self, envelope: EventEnvelope) -> dict | None:
        """Route a webhook event to a docs flow, if it is one."""
        if not settings.agent_docs_enabled:
            return None
        if envelope.event_type == "pull_request":
            if (
                settings.agent_docs_auto_run
                and envelope.event_action in _MERGED_ACTIONS
                and (envelope.payload.get("pull_request") or {}).get("merged")
            ):
                return await self._run_proposal(envelope)
            return None
        if envelope.event_type == "issue_comment":
            if settings.agent_docs_patch_pr_enabled and envelope.event_action in _APPLY_ACTIONS:
                comment = envelope.payload.get("comment") or {}
                body = comment.get("body") or ""
                if body.strip() == _APPLY_COMMAND:
                    return await self._run_apply(envelope)
            return None
        return None

    # ------------------------------------------------------------------
    # Flow 1: propose changelog + doc-drift suggestions on a merged PR
    # ------------------------------------------------------------------
    async def _run_proposal(self, envelope: EventEnvelope) -> dict | None:
        pr = envelope.payload.get("pull_request") or {}
        repo_full_name = envelope.payload.get("repository", {}).get("full_name")
        number = pr.get("number")
        if not repo_full_name or not number:
            return None
        owner, _, repo_name = repo_full_name.partition("/")
        rest = self._rest_client(owner, repo_name)
        changed_files: list[str] = []
        if rest is not None:
            try:
                files = await rest.list_pull_request_files(number)
                changed_files = [(f.get("filename") or "") for f in files if f.get("filename")]
            except Exception:  # noqa: BLE001 - degrade to title-only proposal
                logger.warning(
                    "docs proposal: file list fetch failed repo=%s pr=%s",
                    repo_full_name,
                    number,
                    exc_info=True,
                )

        proposal = self._assistant.analyze(
            pr, changed_files=changed_files, pr_body=pr.get("body") or ""
        )

        comment_posted = False
        comment_skipped = False
        if settings.agent_docs_comments_enabled and rest is not None:
            try:
                comment_posted, comment_skipped = await self._post_proposal(rest, number, proposal)
            except Exception:  # noqa: BLE001 - a comment failure must not fail the event
                logger.warning(
                    "docs proposal comment failed repo=%s pr=%s",
                    repo_full_name,
                    number,
                    exc_info=True,
                )

        outcome = self._record_run(
            envelope, proposal, repo_full_name, comment_posted, comment_skipped
        )
        logger.info(
            "docs proposal done repo=%s pr=%s section=%s doc_updates=%d",
            repo_full_name,
            number,
            proposal.changelog_section,
            len(proposal.doc_updates),
        )
        return outcome

    async def _post_proposal(
        self, rest, pr_number: int, proposal: DocProposal
    ) -> tuple[bool, bool]:
        existing = await rest.list_issue_comments(pr_number, per_page=100)
        if any(_COMMENT_ANCHOR in (comment.get("body") or "") for comment in existing):
            return False, True
        await rest.create_issue_comment(pr_number, format_proposal_comment(proposal))
        return True, False

    # ------------------------------------------------------------------
    # Flow 2: human-approved patch PR (changelog insertion only)
    # ------------------------------------------------------------------
    async def _run_apply(self, envelope: EventEnvelope) -> dict | None:
        comment = envelope.payload.get("comment") or {}
        repo_full_name = envelope.payload.get("repository", {}).get("full_name")
        issue = envelope.payload.get("issue") or {}
        number = _extract_pr_number(issue, comment.get("html_url") or "")
        if not repo_full_name or not number:
            return None
        owner, _, repo_name = repo_full_name.partition("/")
        rest = self._rest_client(owner, repo_name)
        if rest is None:
            logger.warning("docs apply: GitHub not configured, command ignored")
            return None

        try:
            existing = await rest.list_issue_comments(number, per_page=100)
        except Exception:  # noqa: BLE001
            logger.warning("docs apply: comment fetch failed pr=%s", number, exc_info=True)
            return None
        if not any(_COMMENT_ANCHOR in (c.get("body") or "") for c in existing):
            logger.info("docs apply: no proposal anchor on PR %s, refusing", number)
            return self._record_apply_rejected(
                envelope, repo_full_name, number, "no proposal anchor found"
            )

        try:
            pr_data = await rest.get_pull_request(number)
        except Exception:  # noqa: BLE001
            logger.warning("docs apply: PR fetch failed pr=%s", number, exc_info=True)
            return None
        base = (pr_data.get("base") or {}).get("ref") or settings.agent_docs_default_base

        branch = patch_branch_name(number)
        pr_created = await self._create_patch_pr(rest, pr_data, number, base, branch)
        if pr_created is None:
            return None
        outcome = self._record_run(
            envelope, None, repo_full_name, False, False, apply_result=pr_created
        )
        logger.info(
            "docs patch PR opened repo=%s pr=%s branch=%s patch_pr=%s",
            repo_full_name,
            number,
            branch,
            pr_created.get("number"),
        )
        return outcome

    async def _create_patch_pr(
        self, rest, pr_data: dict, pr_number: int, base: str, branch: str
    ) -> dict | None:
        """Create agent/docs-* branch, insert changelog entry, open the patch PR."""
        head_sha = (pr_data.get("head") or {}).get("sha")
        default_sha = (pr_data.get("base") or {}).get("sha")
        if not head_sha:
            return None
        try:
            await rest.create_git_ref(branch, default_sha or head_sha)
        except Exception:  # noqa: BLE001
            logger.warning("docs apply: branch create failed %s", branch, exc_info=True)
            return None

        changelog_path = settings.agent_docs_changelog_path
        try:
            current = await rest.get_file_contents(changelog_path, branch=branch)
            content = base64.b64decode(current.get("content") or "").decode("utf-8")
            sha = current.get("sha")
        except Exception:  # noqa: BLE001
            logger.warning("docs apply: changelog read failed %s", changelog_path, exc_info=True)
            return None
        try:
            proposal = _proposal_from_pr(pr_number, pr_data.get("title") or "")
            if proposal.changelog_entry is None:
                return None
            new_content, inserted = apply_changelog_insertion(
                content, proposal.changelog_section or "", proposal.changelog_entry
            )
            if not inserted or new_content == content:
                return None
            message = f"docs: add changelog entry for PR #{pr_number}"
            await rest.create_or_update_file(changelog_path, new_content, message, branch, sha=sha)
        except Exception:  # noqa: BLE001
            logger.warning("docs apply: changelog write failed pr=%s", pr_number, exc_info=True)
            return None
        try:
            body = (
                f"Automated doc patch proposed by the AI agent for merged PR #{pr_number}: "
                f"'{pr_data.get('title') or ''}'.\n\n"
                "Includes the changelog entry. Doc-drift suggestions were listed in the "
                f"proposal comment on #{pr_number} for manual follow-up."
            )
            return await rest.create_pull_request(
                f"docs: changelog entry for PR #{pr_number}",
                branch,
                base,
                body=body,
            )
        except Exception:  # noqa: BLE001
            logger.warning("docs apply: pull request create failed pr=%s", pr_number, exc_info=True)
            return None

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
        except Exception:  # noqa: BLE001 - degrade to offline mode
            logger.warning("docs assistant: installation token unavailable", exc_info=True)
            return None
        return self._token

    def _record_run(
        self,
        envelope: EventEnvelope,
        proposal: DocProposal | None,
        repo_full_name: str,
        comment_posted: bool,
        comment_skipped: bool,
        *,
        apply_result: dict | None = None,
    ) -> dict:
        if apply_result is not None:
            action = "docs.apply"
            head = apply_result.get("head") or {}
            base_ref = apply_result.get("base") or {}
            outcome: dict[str, object] = {
                "repo": repo_full_name,
                "patch_pr_number": apply_result.get("number"),
                "patch_pr_url": apply_result.get("html_url"),
                "branch": head.get("ref"),
                "base": base_ref.get("ref"),
            }
        else:
            action = "docs.propose"
            outcome = {
                "repo": repo_full_name,
                "pr_number": proposal.pr_number if proposal else None,
                "changelog_section": proposal.changelog_section if proposal else None,
                "changelog_entry": proposal.changelog_entry if proposal else None,
                "doc_updates": [
                    {"path": u.doc_path, "kind": u.change_kind}
                    for u in (proposal.doc_updates if proposal else [])
                ],
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
            run.assistant = "docs"
            run.status = "processed"
            run.outcome = json.dumps(outcome)
            db.add(
                AuditLogEntry(
                    delivery_id=envelope.delivery_id,
                    actor="waste-iq-agent",
                    action=action,
                    detail=json.dumps(outcome),
                )
            )
            db.commit()
        finally:
            db.close()
        return outcome

    def _record_apply_rejected(
        self, envelope: EventEnvelope, repo_full_name: str, pr_number: int, reason: str
    ) -> dict:
        outcome = {
            "repo": repo_full_name,
            "pr_number": pr_number,
            "rejected": reason,
        }
        db = self._session_factory()
        try:
            run = db.query(AgentRun).filter(AgentRun.delivery_id == envelope.delivery_id).first()
            if run is None:
                run = AgentRun(
                    delivery_id=envelope.delivery_id,
                    event_type=envelope.event_type,
                    event_action=envelope.event_action,
                    status="skipped",
                )
                db.add(run)
            run.assistant = "docs"
            run.status = "skipped"
            run.outcome = json.dumps(outcome)
            db.add(
                AuditLogEntry(
                    delivery_id=envelope.delivery_id,
                    actor="waste-iq-agent",
                    action="docs.apply",
                    detail=json.dumps(outcome),
                )
            )
            db.commit()
        finally:
            db.close()
        return outcome


def _extract_pr_number(issue: dict, comment_url: str) -> int | None:
    """PR number from an issue_comment payload (comments on PRs target the PR as an issue)."""
    number = issue.get("number")
    if number:
        return int(number)
    match = _PR_URL_RE.search(comment_url or "")
    if match:
        return int(match.group(1))
    return None


def _proposal_from_pr(pr_number: int, title: str) -> DocProposal:
    section, entry = build_changelog_entry(pr_number, title)
    return DocProposal(
        pr_number=pr_number,
        pr_title=title,
        changelog_section=section,
        changelog_entry=entry,
    )

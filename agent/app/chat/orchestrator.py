"""Orchestrator — intent → retrieval → context → agent → grounded answer.

Dispatches each question to the existing services (Repository Context
Service, LLM Intelligence Layer, PR Review Agent, Issue Assistant,
Documentation Agent). It never replaces them and never duplicates their
logic. Every evidence-requiring answer must carry repository references;
answers without evidence are rejected.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field

from app.chat import planner as planner_module
from app.chat.context_builder import (
    build_repository_context,
    chat_references_from_chunks,
)
from app.chat.conversation import ConversationTurn
from app.chat.intent import IntentResult, detect_intent
from app.chat.models import ChatNoEvidenceError, ChatReference, IntentName
from app.chat.planner import Plan, plan_for
from app.chat.response import (
    context_reference_to_chat_reference,
    evidence_ref_to_chat_reference,
    triage_evidence_to_chat_reference,
)
from app.context.di import Container
from app.context.models import ScoredChunk, SearchRequest
from app.core.config import settings
from app.llm.models import (
    AnalyzeRequest,
    ExplainRequest,
    SummarizeRequest,
)
from app.llm.service import LLMService

logger = logging.getLogger(__name__)

_PR_NUMBER_RE = re.compile(r"(?:#|pr\s+)(\d+)", re.IGNORECASE)
_REPOSITORY_RE = re.compile(r"\b([A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*)\b")
_ISSUE_LEAD_RE = re.compile(
    r"^(?:please\s+)?(?:generate|create|write)\s+(?:an\s+)?issue\s+(?:draft\s+)?"
    r"(?:for|about|on|:)?\s*",
    re.IGNORECASE,
)

_HELP_ANSWER = (
    "I did not recognize the question as a repository task. Try: "
    "'Explain dealer approval', 'Where is NotificationService?', "
    "'Summarize Notification Service', 'Review PR #1', "
    "'Generate an issue draft', or 'Generate documentation for the API'."
)


@dataclass
class ChatOutcome:
    """The orchestrator's raw result before response assembly."""

    intent: IntentName
    answer: str
    confidence: float
    references: list[ChatReference] = field(default_factory=list)
    provider: str = ""
    model: str = ""
    cached: bool = False
    latency_ms: int = 0
    grounded: bool = False
    notes: list[str] = field(default_factory=list)
    search_query: str = ""


class ChatOrchestrator:
    """Deterministic dispatch across the existing services."""

    def __init__(
        self,
        container: Container,
        llm_service: LLMService,
        *,
        intent_detector=detect_intent,
        planner=None,
        limit: int = 6,
        repository: str | None = None,
        issue_assistant=None,
        doc_assistant=None,
        review_service=None,
    ) -> None:
        self._container = container
        self._llm = llm_service
        self._intent_detector = intent_detector
        self._limit = limit
        self._repository = repository or settings.agent_chat_repository

        def _planner(detected: IntentResult, question: str, previous_turn: ConversationTurn | None):
            return plan_for(detected, question, previous_turn, limit=self._limit)

        self._planner = planner or _planner

        from app.agents.doc_agent import DocAssistant
        from app.agents.issue_agent import IssueAssistant
        from app.review.review_service import ReviewService

        self._issue_assistant = issue_assistant or IssueAssistant(container)
        self._doc_assistant = doc_assistant or DocAssistant()
        self._review_service = review_service or ReviewService(container=container)

    # ------------------------------------------------------------------
    def handle(
        self,
        question: str,
        *,
        correlation_id: str | None = None,
        previous_turns: list[ConversationTurn] | None = None,
    ) -> ChatOutcome:
        """Answer one question end-to-end (detect → retrieve → dispatch)."""
        t0 = time.monotonic()
        detected = self._intent_detector(question)
        previous_turn = previous_turns[-1] if previous_turns else None
        plan = self._planner(detected, question, previous_turn)

        if plan.agent == planner_module.AGENT_NONE:
            return self._unknown_outcome(detected, plan, t0)

        results = self._retrieve(plan) if plan.requires_evidence else []
        outcome = self._dispatch(plan, detected, question, results, correlation_id)
        outcome.intent = detected.intent
        outcome.search_query = plan.search_query
        outcome.latency_ms = round((time.monotonic() - t0) * 1000)
        if plan.notes:
            outcome.notes = plan.notes + outcome.notes
        if plan.requires_evidence and not outcome.references:
            raise ChatNoEvidenceError(f"no repository evidence found to answer: {plan.description}")
        logger.info(
            "chat orchestrated",
            extra={
                "intent": outcome.intent,
                "query": plan.search_query,
                "results": len(results),
                "references": len(outcome.references),
                "grounded": outcome.grounded,
                "latency_ms": outcome.latency_ms,
                "correlation_id": correlation_id,
            },
        )
        return outcome

    # ------------------------------------------------------------------
    def _unknown_outcome(self, detected: IntentResult, plan: Plan, t0: float) -> ChatOutcome:
        return ChatOutcome(
            intent=detected.intent,
            answer=_HELP_ANSWER,
            confidence=detected.confidence,
            latency_ms=round((time.monotonic() - t0) * 1000),
            grounded=False,
            notes=[plan.description],
        )

    def _retrieve(self, plan: Plan) -> list[ScoredChunk]:
        response = self._container.search_service().hybrid_search(
            SearchRequest(
                query=plan.search_query,
                limit=plan.limit,
                source_types=plan.source_types,
            )
        )
        return response.results

    # ------------------------------------------------------------------
    def _dispatch(
        self,
        plan: Plan,
        detected: IntentResult,
        question: str,
        results: list[ScoredChunk],
        correlation_id: str | None,
    ) -> ChatOutcome:
        if plan.agent == planner_module.AGENT_LLM_EXPLAIN:
            return self._explain(plan, question, results, correlation_id)
        if plan.agent == planner_module.AGENT_LLM_SUMMARIZE:
            return self._summarize(plan, question, results, correlation_id)
        if plan.agent == planner_module.AGENT_ISSUE:
            return self._issue(plan, question, results)
        if plan.agent == planner_module.AGENT_DOCS:
            return self._documentation(plan, detected, question, results)
        if plan.agent == planner_module.AGENT_REVIEW:
            return self._review(question, correlation_id)
        return ChatOutcome(
            intent=detected.intent,
            answer="unsupported plan",
            confidence=0.0,
            grounded=False,
            notes=[f"no dispatch for agent {plan.agent}"],
        )

    # ------------------------------------------------------------------
    def _context_and_evidence(self, results: list[ScoredChunk]):
        indexed = set(self._container.store().indexed_files())
        return build_repository_context(results, indexed)

    def _explain(
        self,
        plan: Plan,
        question: str,
        results: list[ScoredChunk],
        correlation_id: str | None,
    ) -> ChatOutcome:
        context = self._context_and_evidence(results)
        response = self._llm.explain(
            ExplainRequest(
                repository=self._repository,
                question=question,
                context=context,
            ),
            correlation_id=correlation_id,
        )
        return ChatOutcome(
            intent=plan.intent,
            answer=response.explanation,
            confidence=response.confidence,
            references=[evidence_ref_to_chat_reference(ref) for ref in response.references],
            provider=response.provider,
            model=response.model,
            cached=response.cached,
            grounded=True,
            notes=[f"evidence chunks: {len(results)}"],
        )

    def _summarize(
        self,
        plan: Plan,
        question: str,
        results: list[ScoredChunk],
        correlation_id: str | None,
    ) -> ChatOutcome:
        context = self._context_and_evidence(results)
        response = self._llm.summarize(
            SummarizeRequest(
                repository=self._repository,
                question=question,
                context=context,
            ),
            correlation_id=correlation_id,
        )
        key_points = "\n".join(f"- {point}" for point in response.key_points)
        answer = response.overview + (f"\n{key_points}" if key_points else "")
        return ChatOutcome(
            intent=plan.intent,
            answer=answer,
            confidence=response.confidence,
            references=[evidence_ref_to_chat_reference(ref) for ref in response.references],
            provider=response.provider,
            model=response.model,
            cached=response.cached,
            grounded=True,
            notes=[f"evidence chunks: {len(results)}"],
        )

    def _issue(
        self,
        plan: Plan,
        question: str,
        results: list[ScoredChunk],
    ) -> ChatOutcome:
        number, subject = _parse_issue_subject(question)
        triage = self._issue_assistant.analyze(
            {"number": number, "title": subject or question, "body": question}
        )
        answer = _format_triage(triage)
        references = [triage_evidence_to_chat_reference(evidence) for evidence in triage.evidence]
        return ChatOutcome(
            intent=plan.intent,
            answer=answer,
            confidence=0.95 if references else 0.0,
            references=references,
            provider="issue_assistant",
            grounded=bool(references),
            notes=[f"evidence chunks: {len(results)}"],
        )

    def _documentation(
        self,
        plan: Plan,
        detected: IntentResult,
        question: str,
        results: list[ScoredChunk],
    ) -> ChatOutcome:
        number, _subject = _parse_issue_subject(question)
        changed_files = sorted({chunk.path for chunk in results})
        proposal = self._doc_assistant.analyze(
            {"number": number, "title": detected.subject or question},
            changed_files=changed_files,
            pr_body=question,
        )
        references = chat_references_from_chunks(results)
        answer = proposal.summary
        if proposal.changelog_entry:
            answer += f"\nChangelog ({proposal.changelog_section}): {proposal.changelog_entry}"
        return ChatOutcome(
            intent=plan.intent,
            answer=answer,
            confidence=0.95 if references else 0.0,
            references=references,
            provider="doc_assistant",
            grounded=bool(references),
            notes=[f"changed files: {len(changed_files)}"],
        )

    def _review(self, question: str, correlation_id: str | None) -> ChatOutcome:
        from app.review.review_models import ReviewRequest

        pr_number = _parse_pr_number(question)
        repository = _parse_repository(question)
        if repository is None:
            # Unqualified review questions keep the built-in demo behavior:
            # the configured fixture repository, unless the chat default is
            # already a full "owner/repo" identifier.
            repository = (
                self._repository
                if "/" in (self._repository or "")
                else settings.agent_review_fixture_repo
            )
        review = self._review_service.submit(
            ReviewRequest(repository=repository, pr_number=pr_number, source="chat"),
            correlation_id=correlation_id,
        )
        references = [
            context_reference_to_chat_reference(ref)
            for ref in review.repository_context.related_files
        ]
        response = self._llm.analyze(
            AnalyzeRequest(
                repository=repository,
                question=f"Summarize the review findings for PR #{pr_number}.",
                focus=f"PR #{pr_number} review findings",
                findings=review.findings,
                context=review.repository_context,
            ),
            correlation_id=correlation_id,
        )
        counts = ", ".join(
            f"{category} x {review.summary.counts_by_category.get(category, 0)}"
            for category in sorted(review.summary.counts_by_category)
        )
        answer = f"{response.summary}\n" f"Findings: {review.summary.total} ({counts or 'none'})"
        llm_references = [evidence_ref_to_chat_reference(ref) for ref in response.references]
        return ChatOutcome(
            intent="review_pr",
            answer=answer,
            confidence=response.confidence,
            references=references + llm_references,
            provider=response.provider,
            model=response.model,
            cached=response.cached,
            grounded=True,
            notes=[f"findings: {review.summary.total}"],
        )


def _parse_pr_number(question: str) -> int:
    match = _PR_NUMBER_RE.search(question)
    return int(match.group(1)) if match else 1


def _parse_repository(question: str) -> str | None:
    """Extract a full ``owner/repo`` identifier, e.g. ``Subhajitdas99/waste-iq``."""
    match = _REPOSITORY_RE.search(question)
    return match.group(1) if match else None


def _parse_issue_subject(question: str) -> tuple[int, str]:
    match = _PR_NUMBER_RE.search(question)
    number = int(match.group(1)) if match else 0
    subject = _ISSUE_LEAD_RE.sub("", question).strip()
    return number, subject


def _format_triage(triage) -> str:
    lines = [
        f"Triage for #{triage.issue_number}: {triage.title}",
        f"- Priority: {triage.priority}",
        f"- Labels: {', '.join(triage.suggested_labels) or 'none suggested'}",
        f"- Milestone: {triage.milestone or 'none'}",
        f"- Duplicates: {', '.join(str(d.get('number')) for d in triage.duplicate_of) or 'none'}",
        f"- Evidence: {len(triage.evidence)} repository reference(s)",
    ]
    return "\n".join(lines)

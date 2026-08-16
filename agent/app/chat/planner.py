"""Plan generation — intent to retrieval + agent dispatch plan (Phase 5).

The planner decides *which* existing service answers the question and *what*
to retrieve so that only the required chunks reach the LLM. It never calls
the LLM and never executes anything.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.chat.conversation import ConversationTurn, resolve_query
from app.chat.intent import IntentResult
from app.chat.models import IntentName

AGENT_NONE = "none"
AGENT_LLM_EXPLAIN = "llm_explain"
AGENT_LLM_SUMMARIZE = "llm_summarize"
AGENT_LLM_ANALYZE = "llm_analyze"
AGENT_ISSUE = "issue_assistant"
AGENT_DOCS = "doc_assistant"
AGENT_REVIEW = "review_agent"


@dataclass(frozen=True)
class Plan:
    """What the orchestrator should do for one question."""

    intent: IntentName
    search_query: str
    limit: int
    source_types: list[str] | None
    agent: str
    requires_evidence: bool
    description: str
    notes: list[str] = field(default_factory=list)


_HELP_ANSWER = (
    "I can answer questions about this repository. Try: "
    "'Explain dealer approval', 'Where is NotificationService?', "
    "'Summarize Notification Service', 'Review PR #1', "
    "'Generate an issue draft', or 'Generate documentation for the API'."
)


def help_answer() -> str:
    return _HELP_ANSWER


def plan_for(
    detected: IntentResult,
    question: str,
    previous_turn: ConversationTurn | None = None,
    limit: int = 6,
) -> Plan:
    """Build the dispatch plan for a detected intent (deterministic)."""
    subject = detected.subject
    query, used_followup = resolve_query(question, subject, previous_turn)
    notes: list[str] = ["follow-up: reusing previous search context"] if used_followup else []

    if detected.intent == "unknown":
        return Plan(
            intent="unknown",
            search_query="",
            limit=0,
            source_types=None,
            agent=AGENT_NONE,
            requires_evidence=False,
            description="intent not recognized — present capabilities",
            notes=notes,
        )

    plans: dict[IntentName, Plan] = {
        "explain_architecture": Plan(
            intent=detected.intent,
            search_query=f"{query} architecture",
            limit=limit,
            source_types=None,
            agent=AGENT_LLM_EXPLAIN,
            requires_evidence=True,
            description="retrieve code + docs, explain with the LLM layer",
            notes=notes,
        ),
        "explain_code": Plan(
            intent=detected.intent,
            search_query=query,
            limit=limit,
            source_types=["code"],
            agent=AGENT_LLM_EXPLAIN,
            requires_evidence=True,
            description="retrieve code chunks, explain with the LLM layer",
            notes=notes,
        ),
        "find_implementation": Plan(
            intent=detected.intent,
            search_query=query,
            limit=limit,
            source_types=["code"],
            agent=AGENT_LLM_EXPLAIN,
            requires_evidence=True,
            description="retrieve code chunks, explain where the implementation lives",
            notes=notes,
        ),
        "repository_search": Plan(
            intent=detected.intent,
            search_query=query or question,
            limit=limit,
            source_types=None,
            agent=AGENT_LLM_EXPLAIN,
            requires_evidence=True,
            description="retrieve matching chunks, summarize the hits",
            notes=notes,
        ),
        "summarize_changes": Plan(
            intent=detected.intent,
            search_query=query,
            limit=limit,
            source_types=None,
            agent=AGENT_LLM_SUMMARIZE,
            requires_evidence=True,
            description="retrieve code + docs, summarize with the LLM layer",
            notes=notes,
        ),
        "generate_issue": Plan(
            intent=detected.intent,
            search_query=query or question,
            limit=limit,
            source_types=None,
            agent=AGENT_ISSUE,
            requires_evidence=True,
            description="retrieve triage evidence, run the Issue Assistant",
            notes=notes,
        ),
        "generate_documentation": Plan(
            intent=detected.intent,
            search_query=query,
            limit=limit,
            source_types=None,
            agent=AGENT_DOCS,
            requires_evidence=True,
            description="retrieve touched files, run the Documentation Agent",
            notes=notes,
        ),
        "review_pr": Plan(
            intent=detected.intent,
            search_query=query or question,
            limit=2,
            source_types=None,
            agent=AGENT_REVIEW,
            requires_evidence=True,
            description="run the PR Review Agent, analyze findings with the LLM layer",
            notes=notes,
        ),
    }
    return plans[detected.intent]

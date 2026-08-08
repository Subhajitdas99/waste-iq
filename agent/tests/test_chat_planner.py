"""Unit tests for the chat planner and follow-up query resolution (Phase 5)."""

import pytest

from app.chat.conversation import ConversationTurn, resolve_query
from app.chat.intent import detect_intent
from app.chat.planner import (
    AGENT_DOCS,
    AGENT_ISSUE,
    AGENT_LLM_EXPLAIN,
    AGENT_LLM_SUMMARIZE,
    AGENT_NONE,
    AGENT_REVIEW,
    help_answer,
    plan_for,
)


def _detect(question: str):
    return detect_intent(question)


def _turn(search_query: str = "", intent: str = "explain_code") -> ConversationTurn:
    return ConversationTurn(
        question="previous",
        intent=intent,  # type: ignore[arg-type]
        answer="ok",
        search_query=search_query,
    )


def test_unknown_intent_has_no_agent():
    plan = plan_for(_detect("hello there"), "hello there")
    assert plan.agent == AGENT_NONE
    assert not plan.requires_evidence
    assert plan.limit == 0


def test_explain_code_plan_targets_code_only():
    plan = plan_for(
        _detect("Explain how dealer approval works"), "Explain how dealer approval works"
    )
    assert plan.agent == AGENT_LLM_EXPLAIN
    assert plan.source_types == ["code"]
    assert plan.requires_evidence
    assert "dealer approval" in plan.search_query


def test_explain_architecture_plan_searches_code_and_docs():
    plan = plan_for(
        _detect("Explain the dealer approval workflow"), "Explain the dealer approval workflow"
    )
    assert plan.agent == AGENT_LLM_EXPLAIN
    assert plan.source_types is None
    assert plan.search_query.endswith("architecture")


def test_summarize_plan_uses_llm_summarize():
    plan = plan_for(
        _detect("Summarize the notification service"), "Summarize the notification service"
    )
    assert plan.agent == AGENT_LLM_SUMMARIZE
    assert plan.requires_evidence


def test_issue_plan_routes_to_issue_assistant():
    plan = plan_for(
        _detect("Generate an issue draft for the crash"),
        "Generate an issue draft for the crash",
    )
    assert plan.agent == AGENT_ISSUE
    assert plan.requires_evidence


def test_documentation_plan_routes_to_doc_assistant():
    plan = plan_for(
        _detect("Generate documentation for the API"),
        "Generate documentation for the API",
    )
    assert plan.agent == AGENT_DOCS
    assert plan.requires_evidence


def test_review_plan_routes_to_review_agent_with_small_limit():
    plan = plan_for(_detect("Review PR #3"), "Review PR #3")
    assert plan.agent == AGENT_REVIEW
    assert plan.limit == 2
    assert plan.requires_evidence


def test_plan_honors_limit_override():
    plan = plan_for(_detect("Where is the service?"), "Where is the service?", limit=9)
    assert plan.limit == 9


def test_followup_with_known_intent_reuses_previous_search_query():
    previous = _turn(search_query="dealer approval")
    plan = plan_for(_detect("what does it do?"), "what does it do?", previous_turn=previous)
    assert plan.search_query == "dealer approval"
    assert "follow-up" in " ".join(plan.notes)


def test_unknown_intent_followup_stays_help():
    previous = _turn(search_query="dealer approval")
    plan = plan_for(_detect("what about it?"), "what about it?", previous_turn=previous)
    assert plan.agent == AGENT_NONE
    assert plan.search_query == ""


def test_no_followup_context_falls_back_to_question():
    plan = plan_for(_detect("what about it?"), "what about it?", previous_turn=None)
    assert plan.search_query == ""


def test_help_answer_lists_capabilities():
    text = help_answer()
    assert "Review PR #1" in text
    assert "Explain" in text


def test_resolve_query_subject_wins():
    query, used = resolve_query("Where is the JWT service?", "jwt service", None)
    assert (query, used) == ("jwt service", False)


def test_resolve_query_followup_reuses_previous():
    previous = _turn(search_query="token refresh")
    query, used = resolve_query("what about it?", "", previous)
    assert (query, used) == ("token refresh", True)


def test_resolve_query_no_context_uses_question():
    query, used = resolve_query("what about it?", "", None)
    assert (query, used) == ("what about it?", False)


def test_plan_is_frozen():
    plan = plan_for(_detect("Where is the service?"), "Where is the service?")
    with pytest.raises(Exception):
        plan.agent = AGENT_NONE  # type: ignore[misc]

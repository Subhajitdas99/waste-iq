"""Unit tests for chat response assembly (Phase 5)."""

from app.agents.issue_agent import TriageEvidence
from app.chat.models import ChatReference
from app.chat.response import (
    build_chat_response,
    context_reference_to_chat_reference,
    evidence_ref_to_chat_reference,
    triage_evidence_to_chat_reference,
)
from app.llm.models import EvidenceRef
from app.review.review_models import ContextReference


def test_evidence_ref_to_chat_reference():
    ref = EvidenceRef(
        file_path="src/app.py",
        start_line=4,
        end_line=9,
        chunk_id="chunk:src/app.py:4",
        evidence_id="code:src/app.py:4",
    )
    chat = evidence_ref_to_chat_reference(ref)
    assert chat.file_path == "src/app.py"
    assert chat.evidence_id == "code:src/app.py:4"
    assert chat.source_type == "code"


def test_triage_evidence_to_chat_reference():
    evidence = TriageEvidence(path="src/app.py", start_line=4, end_line=9, score=0.8)
    chat = triage_evidence_to_chat_reference(evidence)
    assert chat.file_path == "src/app.py"
    assert chat.evidence_id == "code:src/app.py:4"
    assert chat.chunk_id == "chunk:src/app.py:4"


def test_context_reference_to_chat_reference_code():
    ref = ContextReference(
        path="src/app.py", start_line=4, end_line=9, section_title=None, score=0.5, snippet=None
    )
    chat = context_reference_to_chat_reference(ref)
    assert chat.evidence_id == "code:src/app.py:4"


def test_context_reference_to_chat_reference_docs():
    ref = ContextReference(
        path="docs/guide.md",
        start_line=2,
        end_line=5,
        section_title=None,
        score=0.5,
        snippet=None,
        source_type="docs",
    )
    chat = context_reference_to_chat_reference(ref)
    assert chat.evidence_id == "docs:docs/guide.md:2-5"


def test_build_chat_response_envelope():
    references = [ChatReference(file_path="src/app.py", start_line=1, end_line=2)]
    response = build_chat_response(
        intent="explain_code",
        answer="the answer",
        confidence=0.9,
        references=references,
        provider="mock",
        model="mock-model",
        cached=False,
        latency_ms=12,
        conversation_id="abc123",
        correlation_id="corr-1",
        grounded=True,
        notes=["note"],
    )
    assert response.intent == "explain_code"
    assert response.answer == "the answer"
    assert response.references == references
    assert response.conversation_id == "abc123"
    assert response.correlation_id == "corr-1"
    assert response.grounded
    assert response.notes == ["note"]


def test_build_chat_response_defaults():
    response = build_chat_response(
        intent="unknown",
        answer="help",
        confidence=0.1,
        references=[],
        provider="",
        model="",
        cached=False,
        latency_ms=0,
        conversation_id=None,
        correlation_id=None,
        grounded=False,
    )
    assert response.notes == []
    assert response.conversation_id is None

"""Response assembly — raw agent output becomes a grounded ChatResponse."""

from __future__ import annotations

from app.agents.issue_agent import TriageEvidence
from app.chat.models import ChatReference, ChatResponse, IntentName
from app.llm.models import EvidenceRef
from app.review.review_models import ContextReference


def evidence_ref_to_chat_reference(ref: EvidenceRef) -> ChatReference:
    """Convert an LLM-layer evidence reference into a chat citation."""
    return ChatReference(
        file_path=ref.file_path,
        start_line=ref.start_line,
        end_line=ref.end_line,
        chunk_id=ref.chunk_id,
        evidence_id=ref.evidence_id,
        source_type="code",
    )


def triage_evidence_to_chat_reference(evidence: TriageEvidence) -> ChatReference:
    """Convert Issue Assistant triage evidence into a chat citation."""
    return ChatReference(
        file_path=evidence.path,
        start_line=evidence.start_line,
        end_line=evidence.end_line,
        chunk_id=f"chunk:{evidence.path}:{evidence.start_line}",
        evidence_id=f"code:{evidence.path}:{evidence.start_line}",
        source_type="code",
    )


def context_reference_to_chat_reference(ref: ContextReference) -> ChatReference:
    """Convert a review RepositoryContext reference into a chat citation."""
    start = ref.start_line or 1
    end = ref.end_line or start
    source_type = ref.source_type or "code"
    if source_type == "code":
        evidence_id = f"code:{ref.path}:{start}"
    else:
        evidence_id = f"{source_type}:{ref.path}:{start}-{end}"
    return ChatReference(
        file_path=ref.path,
        start_line=start,
        end_line=end,
        chunk_id=f"chunk:{ref.path}:{start}",
        evidence_id=evidence_id,
        source_type=source_type,
    )


def build_chat_response(
    *,
    intent: IntentName,
    answer: str,
    confidence: float,
    references: list[ChatReference],
    provider: str,
    model: str,
    cached: bool,
    latency_ms: int,
    conversation_id: str | None,
    correlation_id: str | None,
    grounded: bool,
    notes: list[str] | None = None,
) -> ChatResponse:
    """Assemble the final conversational response envelope."""
    return ChatResponse(
        intent=intent,
        answer=answer,
        confidence=confidence,
        references=references,
        provider=provider,
        model=model,
        cached=cached,
        latency_ms=latency_ms,
        conversation_id=conversation_id,
        correlation_id=correlation_id,
        grounded=grounded,
        notes=notes or [],
    )

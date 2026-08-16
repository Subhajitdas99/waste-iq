"""Context builder — retrieved chunks become the RepositoryContext.

Only retrieved evidence is assembled: code, docs, ADRs, roadmap, and review
findings. The RepositoryContext is the exact contract the LLM layer and the
grounding validator already consume — no new evidence shapes.
"""

from __future__ import annotations

from app.chat.models import ChatReference
from app.context.models import ScoredChunk
from app.llm.grounding import EvidenceEntry
from app.review.review_models import ContextReference, RepositoryContext

_ADR_MARKERS = ("architecture", "adr")
_ROADMAP_MARKERS = ("roadmap", "backlog", "milestone")


def classify_chunk(chunk: ScoredChunk) -> str:
    """Map a retrieved chunk to its RepositoryContext bucket."""
    path = chunk.path.lower()
    if chunk.source_type == "docs":
        if any(marker in path for marker in _ROADMAP_MARKERS):
            return "roadmap"
        if any(marker in path for marker in _ADR_MARKERS):
            return "adr"
        return "docs"
    return "code"


def _reference(chunk: ScoredChunk) -> ContextReference:
    return ContextReference(
        path=chunk.path,
        start_line=chunk.start_line,
        end_line=chunk.end_line,
        section_title=chunk.section_title,
        score=chunk.score,
        snippet=None,
        source_type=chunk.source_type,
    )


def build_repository_context(
    results: list[ScoredChunk],
    indexed_files: set[str] | None = None,
) -> RepositoryContext:
    """Assemble a RepositoryContext from the retrieved chunks only."""
    buckets: dict[str, list[ContextReference]] = {
        "related_files": [],
        "related_docs": [],
        "related_adrs": [],
        "related_roadmap": [],
        "similar_code": [],
    }
    bucket_map = {
        "code": "related_files",
        "docs": "related_docs",
        "adr": "related_adrs",
        "roadmap": "related_roadmap",
    }
    for chunk in results:
        bucket = bucket_map.get(classify_chunk(chunk))
        if bucket is not None:
            buckets[bucket].append(_reference(chunk))
    indexed = sorted(indexed_files or set())
    return RepositoryContext(
        has_context=bool(results),
        related_files=buckets["related_files"],
        related_docs=buckets["related_docs"],
        related_adrs=buckets["related_adrs"],
        related_roadmap=buckets["related_roadmap"],
        similar_code=buckets["similar_code"],
        test_files_known=[path for path in indexed if "test" in path.lower()],
    )


def evidence_entries_from_chunks(results: list[ScoredChunk]) -> list[EvidenceEntry]:
    """Build the evidence universe entries for the retrieved chunks.

    The evidence ids follow the same format as ``grounding._context_entries``
    so the LLM layer's validation matches them by path and line range.
    """
    entries: list[EvidenceEntry] = []
    seen: set[str] = set()
    for chunk in results:
        start = chunk.start_line or 1
        end = chunk.end_line or start
        source_type = classify_chunk(chunk)
        if source_type == "code":
            evidence_id = f"code:{chunk.path}:{start}"
        else:
            evidence_id = f"{source_type}:{chunk.path}:{start}-{end}"
        if evidence_id in seen:
            continue
        seen.add(evidence_id)
        entries.append(
            EvidenceEntry(
                evidence_id=evidence_id,
                chunk_id=chunk.chunk_id,
                path=chunk.path,
                start_line=start,
                end_line=end,
                source_type=source_type,
                snippet=None,
            )
        )
    return entries


def chat_references_from_chunks(results: list[ScoredChunk]) -> list[ChatReference]:
    """Chat-facing citations for the retrieved chunks."""
    references: list[ChatReference] = []
    for chunk in results:
        start = chunk.start_line or 1
        end = chunk.end_line or start
        source_type = classify_chunk(chunk)
        if source_type == "code":
            evidence_id = f"code:{chunk.path}:{start}"
        else:
            evidence_id = f"{source_type}:{chunk.path}:{start}-{end}"
        references.append(
            ChatReference(
                file_path=chunk.path,
                start_line=start,
                end_line=end,
                chunk_id=chunk.chunk_id,
                evidence_id=evidence_id,
                source_type=source_type,
            )
        )
    return references

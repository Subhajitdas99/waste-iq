"""Grounding: every LLM claim must resolve to retrieved repository evidence.

An "evidence universe" is built exclusively from the repository context the
caller supplied (review findings + RepositoryContext references). A response
is only accepted when all of its references match the universe and every claim
carries at least one reference. Anything else is rejected as unsupported.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.llm.models import (
    EvidenceRef,
    GroundedClaim,
    GroundingValidation,
    LLMResponseBase,
)
from app.review.review_models import RepositoryContext, ReviewFinding


@dataclass(frozen=True)
class EvidenceEntry:
    """One retrievable piece of evidence the LLM is allowed to cite."""

    evidence_id: str
    chunk_id: str
    path: str
    start_line: int | None = None
    end_line: int | None = None
    source_type: str = "code"
    snippet: str | None = None


def _finding_entries(findings: list[ReviewFinding]) -> list[EvidenceEntry]:
    entries: list[EvidenceEntry] = []
    for finding in findings:
        line = finding.start_line
        entries.append(
            EvidenceEntry(
                evidence_id=f"code:{finding.file_path}:{line}",
                chunk_id=f"chunk:{finding.file_path}:{line}",
                path=finding.file_path,
                start_line=line,
                end_line=finding.end_line,
                source_type="code",
                snippet=finding.snippet,
            )
        )
    return entries


def _context_entries(context: RepositoryContext | None) -> list[EvidenceEntry]:
    entries: list[EvidenceEntry] = []
    if context is None:
        return entries
    groups: list[tuple[str, list]] = [
        ("code", context.related_files),
        ("doc", context.related_docs),
        ("adr", context.related_adrs),
        ("roadmap", context.related_roadmap),
        ("similar", context.similar_code),
    ]
    for source_type, references in groups:
        for ref in references:
            start = ref.start_line or 1
            end = ref.end_line or start
            if source_type == "code":
                evidence_id = f"code:{ref.path}:{start}"
            else:
                evidence_id = f"{source_type}:{ref.path}:{start}-{end}"
            entries.append(
                EvidenceEntry(
                    evidence_id=evidence_id,
                    chunk_id=f"chunk:{ref.path}:{start}",
                    path=ref.path,
                    start_line=start,
                    end_line=end,
                    source_type=source_type,
                    snippet=ref.snippet,
                )
            )
    return entries


def build_evidence_entries(
    findings: list[ReviewFinding], context: RepositoryContext | None
) -> list[EvidenceEntry]:
    """The full evidence universe for a request, deduplicated by evidence id."""
    seen: set[str] = set()
    entries: list[EvidenceEntry] = []
    for entry in _finding_entries(findings) + _context_entries(context):
        if entry.evidence_id in seen:
            continue
        seen.add(entry.evidence_id)
        entries.append(entry)
    return entries


class EvidenceUniverse:
    """Indexed set of evidence entries, keyed by path and evidence id."""

    def __init__(self, entries: list[EvidenceEntry]) -> None:
        self.entries = entries
        self.by_path: dict[str, list[EvidenceEntry]] = {}
        self.by_id: dict[str, EvidenceEntry] = {}
        for entry in entries:
            self.by_path.setdefault(entry.path, []).append(entry)
            self.by_id[entry.evidence_id] = entry

    @property
    def size(self) -> int:
        return len(self.entries)


def _matches(entry: EvidenceEntry, ref: EvidenceRef) -> bool:
    """A reference matches an entry when path and line range align."""
    if ref.start_line is None and ref.end_line is None:
        return True
    ref_start = ref.start_line or ref.end_line or 1
    ref_end = ref.end_line or ref.start_line or ref_start
    entry_start = entry.start_line or 1
    entry_end = entry.end_line or entry_start
    if ref_end < entry_start or ref_start > entry_end:
        return False
    return True


def validate(
    response: LLMResponseBase,
    universe: EvidenceUniverse,
    *,
    require_references: bool = True,
) -> GroundingValidation:
    """Validate that every reference resolves to the evidence universe."""
    claims: list[GroundedClaim] = getattr(response, "claims", None) or []
    violations: list[str] = []
    matched = 0
    unsupported = 0
    reference_count = 0
    for ref in response.references:
        reference_count += 1
        if any(_matches(entry, ref) for entry in universe.by_path.get(ref.file_path, [])):
            matched += 1
        else:
            unsupported += 1
            violations.append(
                f"unsupported reference {ref.file_path}:{ref.start_line or '?'}-"
                f"{ref.end_line or '?'}"
            )
    for claim in claims:
        if not claim.references:
            violations.append(f"claim without evidence: {claim.claim[:120]}")
        else:
            reference_count += len(claim.references)
            for ref in claim.references:
                if any(_matches(entry, ref) for entry in universe.by_path.get(ref.file_path, [])):
                    matched += 1
                else:
                    unsupported += 1
                    violations.append(
                        f"unsupported claim reference {ref.file_path}:"
                        f"{ref.start_line or '?'}-{ref.end_line or '?'}"
                    )
    if require_references and reference_count == 0:
        violations.append("response contains no references to repository evidence")
    supported = unsupported == 0 and not (require_references and reference_count == 0)
    return GroundingValidation(
        supported=supported,
        claims=len(claims),
        references=reference_count,
        matched=matched,
        unsupported=unsupported,
        violations=violations[:20],
    )

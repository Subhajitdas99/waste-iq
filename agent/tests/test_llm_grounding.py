"""Tests for evidence grounding: every reference must resolve to evidence."""

from app.llm.grounding import (
    EvidenceUniverse,
    build_evidence_entries,
    validate,
)
from app.llm.models import AnalyzeResponse, EvidenceRef
from app.review.review_models import ContextReference, RepositoryContext, ReviewFinding


def _finding(path="src/app.py", start=10, end=20):
    return ReviewFinding(
        rule_id="R1",
        category="security",
        severity="high",
        title="title",
        explanation="explanation",
        file_path=path,
        start_line=start,
        end_line=end,
        snippet="password = 'hunter2-secret'",
    )


def _context():
    return RepositoryContext(
        related_files=[ContextReference(path="src/app.py", start_line=10, end_line=20)],
        related_docs=[ContextReference(path="docs/api.md", start_line=1, end_line=5)],
        related_adrs=[ContextReference(path="docs/adr/001.md", start_line=1, end_line=2)],
        related_roadmap=[ContextReference(path="ROADMAP.md", start_line=3, end_line=3)],
        similar_code=[ContextReference(path="src/similar.py", start_line=1, end_line=4)],
    )


def _response(**overrides):
    values = {
        "role": "analyze",
        "summary": "s",
        "references": [EvidenceRef(file_path="src/app.py", start_line=10, end_line=20)],
    }
    values.update(overrides)
    return AnalyzeResponse(**values)


def test_build_evidence_entries_merges_findings_and_context():
    entries = build_evidence_entries([_finding()], _context())
    ids = {entry.evidence_id for entry in entries}
    assert "code:src/app.py:10" in ids
    assert "doc:docs/api.md:1-5" in ids
    assert "adr:docs/adr/001.md:1-2" in ids
    assert "roadmap:ROADMAP.md:3-3" in ids
    assert "similar:src/similar.py:1-4" in ids
    assert len(entries) == 5


def test_build_evidence_entries_deduplicates():
    entries = build_evidence_entries([_finding(), _finding()], None)
    assert len(entries) == 1


def test_build_evidence_entries_empty():
    assert build_evidence_entries([], None) == []


def test_validate_accepts_grounded_response():
    universe = EvidenceUniverse(build_evidence_entries([_finding()], None))
    validation = validate(_response(), universe)
    assert validation.supported is True
    assert validation.references == 1
    assert validation.matched == 1
    assert validation.unsupported == 0
    assert validation.violations == []


def test_validate_rejects_unsupported_file():
    universe = EvidenceUniverse(build_evidence_entries([_finding()], None))
    response = _response(
        references=[EvidenceRef(file_path="src/other.py", start_line=1, end_line=2)]
    )
    validation = validate(response, universe)
    assert validation.supported is False
    assert validation.unsupported == 1
    assert any("unsupported reference src/other.py:1-2" in v for v in validation.violations)


def test_validate_rejects_unsupported_lines():
    universe = EvidenceUniverse(build_evidence_entries([_finding()], None))
    response = _response(
        references=[EvidenceRef(file_path="src/app.py", start_line=100, end_line=200)]
    )
    validation = validate(response, universe)
    assert validation.supported is False


def test_validate_accepts_path_only_reference():
    universe = EvidenceUniverse(build_evidence_entries([_finding()], None))
    response = _response(references=[EvidenceRef(file_path="src/app.py")])
    validation = validate(response, universe)
    assert validation.supported is True
    assert validation.matched == 1


def test_validate_start_line_only_reference():
    universe = EvidenceUniverse(build_evidence_entries([_finding()], None))
    response = _response(references=[EvidenceRef(file_path="src/app.py", start_line=15)])
    assert validate(response, universe).supported is True


def test_validate_rejects_no_references_by_default():
    universe = EvidenceUniverse(build_evidence_entries([_finding()], None))
    response = _response(references=[])
    validation = validate(response, universe)
    assert validation.supported is False
    assert any("no references" in v for v in validation.violations)


def test_validate_allows_no_references_when_not_required():
    universe = EvidenceUniverse(build_evidence_entries([_finding()], None))
    response = _response(references=[])
    validation = validate(response, universe, require_references=False)
    assert validation.supported is True


def test_validate_rejects_claim_without_evidence():
    universe = EvidenceUniverse(build_evidence_entries([_finding()], None))
    response = _response(
        references=[],
        claims=[{"claim": "the database is compromised", "references": []}],
    )
    validation = validate(response, universe)
    assert validation.supported is False
    assert any("claim without evidence" in v for v in validation.violations)


def test_validate_rejects_claim_with_unsupported_reference():
    universe = EvidenceUniverse(build_evidence_entries([_finding()], None))
    response = _response(
        references=[],
        claims=[
            {
                "claim": "claim",
                "references": [{"file_path": "ghost.py", "start_line": 1, "end_line": 2}],
            }
        ],
    )
    validation = validate(response, universe)
    assert validation.supported is False
    assert any("unsupported claim reference ghost.py" in v for v in validation.violations)


def test_validate_counts_multiple_references():
    universe = EvidenceUniverse(build_evidence_entries([_finding()], _context()))
    response = _response(
        references=[
            EvidenceRef(file_path="src/app.py", start_line=10, end_line=20),
            EvidenceRef(file_path="docs/api.md", start_line=1, end_line=5),
        ]
    )
    validation = validate(response, universe)
    assert validation.references == 2
    assert validation.matched == 2
    assert validation.supported is True


def test_validate_accepts_grounded_claims():
    universe = EvidenceUniverse(build_evidence_entries([_finding()], None))
    response = _response(
        references=[],
        claims=[
            {
                "claim": "a claim",
                "references": [{"file_path": "src/app.py", "start_line": 10, "end_line": 20}],
            }
        ],
    )
    validation = validate(response, universe)
    assert validation.supported is True
    assert validation.claims == 1
    assert validation.matched == 1


def test_universe_indexes_by_path_and_id():
    universe = EvidenceUniverse(build_evidence_entries([_finding()], None))
    assert universe.size == 1
    assert "code:src/app.py:10" in universe.by_id
    assert universe.by_path["src/app.py"]

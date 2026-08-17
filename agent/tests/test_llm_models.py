"""Tests for LLM layer typed models."""

import pytest
from pydantic import ValidationError

from app.llm.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    EvidenceRef,
    ExplainRequest,
    ProviderResponse,
    SummarizeRequest,
)


def _request(**overrides):
    values = {"repository": "acme/app", "question": "why?"}
    values.update(overrides)
    return values


def test_analyze_request_minimal():
    request = AnalyzeRequest(repository="acme/app")
    assert request.repository == "acme/app"
    assert request.max_tokens is None


def test_unknown_provider_rejected():
    with pytest.raises(ValidationError):
        AnalyzeRequest(**(_request(provider="amazon")))


def test_known_provider_accepted():
    request = AnalyzeRequest(**(_request(provider="mock")))
    assert request.provider == "mock"


def test_max_tokens_bounds():
    with pytest.raises(ValidationError):
        AnalyzeRequest(**(_request(max_tokens=8)))
    with pytest.raises(ValidationError):
        AnalyzeRequest(**(_request(max_tokens=9000)))
    request = AnalyzeRequest(**(_request(max_tokens=256)))
    assert request.max_tokens == 256


def test_explain_requires_question():
    with pytest.raises(ValidationError):
        ExplainRequest(repository="acme/app")
    with pytest.raises(ValidationError):
        ExplainRequest(repository="acme/app", question="   ")
    request = ExplainRequest(repository="acme/app", question="why?")
    assert request.question == "why?"


def test_summarize_request_no_question_needed():
    request = SummarizeRequest(repository="acme/app")
    assert request.repository == "acme/app"


def test_extra_fields_forbidden_in_requests():
    with pytest.raises(ValidationError):
        AnalyzeRequest(**(_request(hacked_field="x")))


def test_extra_fields_forbidden_in_responses():
    with pytest.raises(ValidationError):
        AnalyzeResponse(role="analyze", summary="s", injected="bad")


def test_confidence_bounded():
    response = AnalyzeResponse(role="analyze", summary="s", confidence=5.0)
    assert response.confidence == 1.0
    response = AnalyzeResponse(role="analyze", summary="s", confidence=-1.0)
    assert response.confidence == 0.0


def test_evidence_ref_validates_lines():
    ref = EvidenceRef(file_path="a.py", start_line=1, end_line=2)
    assert ref.evidence_id is None
    with pytest.raises(ValidationError):
        EvidenceRef(file_path="a.py", start_line=0)
    with pytest.raises(ValidationError):
        EvidenceRef(file_path="")


def test_provider_response_carries_retries():
    response = ProviderResponse(content="{}")
    assert response.retries == 0
    response = ProviderResponse(content="{}", retries=2)
    assert response.retries == 2

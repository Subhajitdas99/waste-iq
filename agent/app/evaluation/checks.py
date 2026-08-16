"""Deterministic LLM-layer checks executed by the benchmark runner."""

from __future__ import annotations

from app.core.config import Settings
from app.evaluation.schema import CaseResult

CHECKED_SERVICES = {
    "grounding_validation": ["build_evidence_entries", "validate"],
    "prompt_quality": ["PromptBuilder.build", "Redactor.redact"],
    "json_validation": ["extract_json", "ResponseParser.parse"],
    "cache_validation": ["hash_request", "MemoryCache"],
    "telemetry": ["Telemetry.record_call", "Telemetry.snapshot"],
    "provider_selection": ["resolve_provider", "build_provider", "MockProvider"],
    "hallucination_rejection": ["validate", "GroundingViolationError"],
}


def _finding(path="src/app.py", start=10, end=20):
    from app.review.review_models import ReviewFinding

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


def _grounded_response():
    from app.llm.models import AnalyzeResponse, EvidenceRef

    return AnalyzeResponse(
        role="analyze",
        summary="s",
        references=[EvidenceRef(file_path="src/app.py", start_line=10, end_line=20)],
    )


def _ghost_response():
    from app.llm.models import AnalyzeResponse, EvidenceRef

    return AnalyzeResponse(
        role="analyze",
        summary="s",
        references=[EvidenceRef(file_path="ghost.py", start_line=1, end_line=2)],
    )


def check_grounding_validation() -> CaseResult:
    from app.llm.grounding import EvidenceUniverse, build_evidence_entries, validate

    universe = EvidenceUniverse(build_evidence_entries([_finding()], None))
    validation = validate(_grounded_response(), universe)
    ok = validation.supported and validation.matched == 1 and validation.unsupported == 0
    return CaseResult(
        case_id="ll-01-grounding-validation",
        actual_answer=(
            f"grounding validation accepted grounded response: "
            f"supported={validation.supported} matched={validation.matched}"
        ),
        cited_services=list(CHECKED_SERVICES["grounding_validation"]),
        evidence_grounded=ok,
        evidence_count=universe.size,
        behaviour_met=ok,
        notes="violations=" + str(len(validation.violations)),
    )


def check_prompt_quality() -> CaseResult:
    from app.llm.models import ExplainRequest
    from app.llm.prompt_builder import PromptBuilder, Redactor

    builder = PromptBuilder()
    request = ExplainRequest(repository="waste-iq", question="What is the repository pattern?")
    built = builder.build("explain", request, findings=[_finding()])
    redacted = Redactor().redact("password = 'hunter2-secret'")
    ok = (
        "evidence" in built.system_prompt.lower()
        and "src/app.py" in built.user_prompt
        and "hunter2-secret" not in redacted
        and built.redactions > 0
    )
    return CaseResult(
        case_id="ll-02-prompt-quality",
        actual_answer=(
            f"prompt built: system={len(built.system_prompt)} chars, "
            f"user={len(built.user_prompt)} chars, redactions={built.redactions}"
        ),
        cited_services=list(CHECKED_SERVICES["prompt_quality"]),
        evidence_grounded=True,
        evidence_count=len(built.evidence),
        behaviour_met=ok,
        notes="redacted secrets" if ok else "prompt quality check failed",
    )


def check_json_validation() -> CaseResult:
    from app.llm.models import MalformedResponseError
    from app.llm.response_parser import ResponseParser, extract_json

    content = '```json\n{"summary": "ok", "role": "analyze"}\n```'
    parsed = extract_json(content)
    response = ResponseParser().parse(
        '{"summary": "ok", "priorities": [], "recommendations": [], "risks": []}',
        "analyze",
    )
    rejected = False
    try:
        ResponseParser().parse("{not json", "analyze")
    except MalformedResponseError:
        rejected = True
    ok = parsed is not None and response is not None and rejected
    return CaseResult(
        case_id="ll-03-json-validation",
        actual_answer=(
            "extract_json ok="
            + str(parsed is not None)
            + ", parse ok="
            + str(response is not None)
            + ", malformed rejected="
            + str(rejected)
        ),
        cited_services=list(CHECKED_SERVICES["json_validation"]),
        evidence_grounded=True,
        evidence_count=1,
        behaviour_met=ok,
        notes="malformed output rejected" if rejected else "malformed output not rejected",
    )


def check_cache_validation() -> CaseResult:
    from app.llm.cache import MemoryCache, hash_request

    cache = MemoryCache()
    key = hash_request("mock", "m", "system", "user")
    same_key = hash_request("mock", "m", "system", "user")
    cache.set(key, "cached-value")
    hit = cache.get(key)
    miss = cache.get("other-key")
    ok = key == same_key and hit == "cached-value" and miss is None
    return CaseResult(
        case_id="ll-04-cache-validation",
        actual_answer=(
            "deterministic hash="
            + str(key == same_key)
            + ", hit="
            + str(hit is not None)
            + ", miss="
            + str(miss is None)
        ),
        cited_services=list(CHECKED_SERVICES["cache_validation"]),
        evidence_grounded=True,
        evidence_count=1,
        behaviour_met=ok,
        notes="cache behaves deterministically" if ok else "cache check failed",
    )


def check_telemetry() -> CaseResult:
    from app.llm.telemetry import Telemetry

    telemetry = Telemetry()
    telemetry.record_call(
        provider="mock",
        latency_ms=5,
        prompt_tokens=10,
        completion_tokens=5,
        failure=False,
        retries=0,
    )
    telemetry.record_call(
        provider="mock",
        latency_ms=7,
        prompt_tokens=20,
        completion_tokens=8,
        failure=False,
        retries=0,
    )
    telemetry.record_cache(hit=True)
    status = telemetry.snapshot(
        enabled=True,
        provider="mock",
        configured=False,
        model="m",
        deterministic_fallback=True,
        cache_backend="memory",
    )
    ok = status.total_calls == 2 and status.cache_hits >= 1
    return CaseResult(
        case_id="ll-05-telemetry",
        actual_answer=(
            f"telemetry snapshot: calls={status.total_calls} cache_hits={status.cache_hits}"
        ),
        cited_services=list(CHECKED_SERVICES["telemetry"]),
        evidence_grounded=True,
        evidence_count=status.total_calls,
        behaviour_met=ok,
        notes="call/cache events recorded" if ok else "telemetry check failed",
    )


def _no_cloud_credentials() -> Settings:
    """Settings with every cloud credential forced to ``None``.

    The benchmark's provider-selection case must be deterministic and
    hermetic: it must not depend on the ambient environment or on a local
    developer ``.env`` (which may carry real keys). ``_env_file=None``
    disables dotenv loading and explicit init kwargs take precedence over
    environment variables, so a real key on the machine can never leak into
    this case.
    """
    return Settings(  # type: ignore[call-arg]
        _env_file=None,
        agent_llm_provider="openrouter",
        agent_llm_model="",
        agent_llm_api_key=None,
        agent_llm_base_url=None,
        agent_openai_api_key=None,
        agent_anthropic_api_key=None,
        agent_google_api_key=None,
        agent_openrouter_api_key=None,
        agent_openrouter_http_referer=None,
        agent_openrouter_app_name=None,
    )


def check_provider_selection() -> CaseResult:
    from app.llm.provider import MockProvider, build_provider, resolve_provider

    hermetic = _no_cloud_credentials()
    name, _configured = resolve_provider(hermetic)
    provider = build_provider(hermetic)
    ok = name == "mock" and isinstance(provider, MockProvider) and _configured is False
    return CaseResult(
        case_id="ll-06-provider-selection",
        actual_answer=f"resolver chose provider={name!r} configured={_configured}",
        cited_services=list(CHECKED_SERVICES["provider_selection"]),
        evidence_grounded=True,
        evidence_count=1,
        behaviour_met=ok,
        notes=(
            "deterministic mock selected without credentials" if ok else "provider selection wrong"
        ),
    )


def check_hallucination_rejection() -> CaseResult:
    from app.llm.grounding import EvidenceUniverse, build_evidence_entries, validate

    universe = EvidenceUniverse(build_evidence_entries([_finding()], None))
    validation = validate(_ghost_response(), universe)
    rejected = not validation.supported and validation.unsupported == 1
    ok = rejected
    return CaseResult(
        case_id="ll-07-hallucination-rejection",
        actual_answer=(
            f"unsupported reference rejected: supported={validation.supported} "
            f"violations={len(validation.violations)}"
        ),
        cited_services=list(CHECKED_SERVICES["hallucination_rejection"]),
        evidence_grounded=ok,
        evidence_count=1,
        hallucinated_citations=["ghost.py:1-2"] if not ok else [],
        behaviour_met=ok,
        notes="hallucination rejected" if ok else "hallucination NOT rejected",
    )


CHECK_HANDLERS = {
    "grounding_validation": check_grounding_validation,
    "prompt_quality": check_prompt_quality,
    "json_validation": check_json_validation,
    "cache_validation": check_cache_validation,
    "telemetry": check_telemetry,
    "provider_selection": check_provider_selection,
    "hallucination_rejection": check_hallucination_rejection,
}

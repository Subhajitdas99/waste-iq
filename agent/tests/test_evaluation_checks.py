"""Tests for the deterministic LLM-layer checks executed by the benchmark runner."""

from app.evaluation.checks import (
    CHECK_HANDLERS,
    check_cache_validation,
    check_hallucination_rejection,
    check_json_validation,
    check_prompt_quality,
    check_provider_selection,
    check_telemetry,
)


def test_prompt_quality_redacts_secrets_and_cites_evidence():
    result = check_prompt_quality()
    assert result.case_id == "ll-02-prompt-quality"
    assert result.behaviour_met is True
    assert "hunter2-secret" not in result.actual_answer
    assert result.evidence_count >= 1


def test_json_validation_accepts_wellformed_and_rejects_malformed():
    result = check_json_validation()
    assert result.case_id == "ll-03-json-validation"
    assert result.behaviour_met is True
    assert "malformed output rejected" in result.notes


def test_cache_validation_is_deterministic():
    result = check_cache_validation()
    assert result.case_id == "ll-04-cache-validation"
    assert result.behaviour_met is True


def test_telemetry_records_calls_and_cache_hits():
    result = check_telemetry()
    assert result.case_id == "ll-05-telemetry"
    assert result.behaviour_met is True
    assert "calls=2" in result.actual_answer


def test_provider_selection_resolves_deterministically():
    result = check_provider_selection()
    assert result.case_id == "ll-06-provider-selection"
    assert "provider=" in result.actual_answer


def test_provider_selection_is_hermetic_against_real_credentials(monkeypatch):
    """A real OpenRouter key in the environment must not flip the case.

    Regression for the benchmark failure: the case previously read the
    app-global settings singleton, so a developer .env with a real
    AGENT_OPENROUTER_API_KEY made the resolver choose openrouter and the
    case FAIL. The check now builds a hermetic Settings object.
    """
    monkeypatch.setenv("AGENT_LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("AGENT_OPENROUTER_API_KEY", "sk-real-key")
    result = check_provider_selection()
    assert result.behaviour_met is True
    assert "provider='mock'" in result.actual_answer
    assert "configured=False" in result.actual_answer


def test_provider_selection_ignores_credentials_in_dotenv(tmp_path, monkeypatch):
    """Even a .env file with real keys on disk cannot leak into the check."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "AGENT_LLM_PROVIDER=openrouter\n"
        "AGENT_OPENROUTER_API_KEY=sk-real-dotenv\n"
        "AGENT_OPENAI_API_KEY=sk-real-openai\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("AGENT_LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("AGENT_OPENROUTER_API_KEY", "sk-real-env")
    monkeypatch.chdir(tmp_path)

    from app.llm.provider import MockProvider, build_provider, resolve_provider

    from app.evaluation.checks import _no_cloud_credentials

    settings = _no_cloud_credentials()
    name, configured = resolve_provider(settings)
    provider = build_provider(settings)
    assert name == "mock"
    assert configured is False
    assert isinstance(provider, MockProvider)


def test_hallucination_rejection_rejects_ghost_citation():
    result = check_hallucination_rejection()
    assert result.case_id == "ll-07-hallucination-rejection"
    assert result.behaviour_met is True
    assert "violations=" in result.actual_answer


def test_all_checks_execute_and_register_case_ids():
    results = {name: handler() for name, handler in CHECK_HANDLERS.items()}
    assert len(results) == 7
    for name, result in results.items():
        assert result.case_id
        assert result.actual_answer
        assert result.cited_services

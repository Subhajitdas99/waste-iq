"""Tests for prompt building: evidence-only, redacted, role-shaped prompts."""

from app.llm.prompt_builder import PromptBuilder, Redactor
from app.llm.models import AnalyzeRequest, ExplainRequest, SummarizeRequest
from app.review.review_models import ContextReference, RepositoryContext, ReviewFinding


def _finding(path="src/app.py", start=10, end=20, snippet=None):
    return ReviewFinding(
        rule_id="R1",
        category="security",
        severity="high",
        title="Hardcoded secret",
        explanation="Password is hardcoded",
        file_path=path,
        start_line=start,
        end_line=end,
        snippet=snippet or "password = 'hunter2-secret'",
    )


def _context():
    return RepositoryContext(
        related_files=[ContextReference(path="src/app.py", start_line=10, end_line=20)],
        related_docs=[ContextReference(path="docs/api.md", start_line=1, end_line=5)],
    )


def _analyze_request(**overrides):
    values = {
        "repository": "acme/app",
        "findings": [_finding()],
        "context": _context(),
        "rules_used": ["R1"],
    }
    values.update(overrides)
    return AnalyzeRequest(**values)


def test_builder_returns_role_specific_system_prompt():
    builder = PromptBuilder()
    built = builder.build("analyze", _analyze_request())
    assert "Role instruction" in built.system_prompt
    assert '"summary"' in built.system_prompt
    assert built.redactions >= 0


def test_builder_embeds_evidence_block_with_ids():
    built = PromptBuilder().build("analyze", _analyze_request())
    assert "evidence_id: code:src/app.py:10" in built.user_prompt
    assert "chunk_id: chunk:src/app.py:10" in built.user_prompt
    assert "file: src/app.py" in built.user_prompt
    assert "lines: 10-20" in built.user_prompt
    assert "EVIDENCE (the only files/lines you may reference)" in built.user_prompt


def test_builder_redacts_secrets_in_snippets_and_questions():
    builder = PromptBuilder()
    request = _analyze_request(question="What is my token sk-ABCDEFGHIJKLMNOPQRSTUV?")
    built = builder.build("analyze", request)
    assert "sk-ABCDEFGHIJKLMNOPQRSTUV" not in built.user_prompt
    assert "[REDACTED:API-KEY]" in built.user_prompt
    assert built.redactions >= 1


def test_builder_redacts_password_snippet():
    built = PromptBuilder().build("analyze", _analyze_request())
    assert "hunter2-secret" not in built.user_prompt
    assert "[REDACTED]" in built.user_prompt


def test_builder_caps_prompt_size():
    builder = PromptBuilder(max_input_tokens=60)
    built = builder.build("analyze", _analyze_request())
    assert "[truncated]" in built.user_prompt


def test_builder_explain_includes_question():
    request = ExplainRequest(repository="acme/app", question="How does retry work?", findings=[])
    built = PromptBuilder().build("explain", request)
    assert "# Role: explain" in built.user_prompt
    assert "How does retry work?" in built.user_prompt


def test_builder_summarize_uses_summarize_role():
    request = SummarizeRequest(repository="acme/app", findings=[])
    built = PromptBuilder().build("summarize", request)
    assert "# Role: summarize" in built.user_prompt


def test_builder_evidence_is_deduped_across_findings_and_context():
    built = PromptBuilder().build("analyze", _analyze_request())
    assert built.user_prompt.count("evidence_id: code:src/app.py:10") == 1


def test_builder_no_context_note():
    request = AnalyzeRequest(repository="acme/app", findings=[])
    built = PromptBuilder().build("analyze", request)
    assert "no repository context supplied" in built.user_prompt
    assert "# Review findings:" not in built.user_prompt


def test_redactor_scrubs_bearer_and_jwt():
    redactor = Redactor()
    redactor = Redactor()
    text = (
        "Bearer abcdefghijklmnopqrstuvwxyz + "
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0."
        "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    )
    redacted = redactor.redact(text)
    assert "[REDACTED:BEARER]" in redacted
    assert "[REDACTED:JWT]" in redacted
    assert redactor.count(text) >= 2


def test_redactor_handles_none():
    redactor = Redactor()
    assert redactor.redact(None) == ""
    assert redactor.count(None) == 0


def test_redactor_auth_header():
    redactor = Redactor()
    redacted = redactor.redact("authorization: ghp_somegithubtokenthatislongenough123456")
    assert "ghp_somegithubtokenthatislongenough123456" not in redacted
    assert "authorization: [REDACTED]" in redacted

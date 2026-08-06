"""Unit tests for deterministic intent detection (Phase 5)."""

from app.chat.intent import detect_intent


def _intent(question: str) -> str:
    return detect_intent(question).intent


def test_review_pr_variants():
    for q in (
        "Review PR #12",
        "Please review this pull request",
        "review the pr",
        "pr review for #5",
        "can you review pull request #3",
    ):
        assert _intent(q) == "review_pr", q


def test_generate_issue_variants():
    for q in (
        "Generate an issue draft for the crash",
        "create issue for the payment bug",
        "write issue about the timeout",
        "triage issue #42",
    ):
        assert _intent(q) == "generate_issue", q


def test_generate_documentation_variants():
    for q in (
        "Generate documentation for the API",
        "write documentation for dealer approval",
        "generate changelog for the release",
        "update docs for the service",
    ):
        assert _intent(q) == "generate_documentation", q


def test_summarize_variants():
    for q in (
        "Summarize the notification service",
        "summarise the marketplace",
        "summary of the changes",
        "what changed in this pr",
    ):
        assert _intent(q) == "summarize_changes", q


def test_explain_architecture_variants():
    for q in (
        "Explain the dealer approval workflow",
        "What is the architecture?",
        "show me the system design",
        "which ADRs exist",
    ):
        assert _intent(q) == "explain_architecture", q


def test_find_implementation_variants():
    for q in (
        "Where is NotificationService?",
        "which file implements the JWT service",
        "find implementation of the token refresh",
        "locate the calculator module",
    ):
        assert _intent(q) == "find_implementation", q


def test_explain_code_variants():
    for q in (
        "Explain how dealer approval works",
        "what does the review engine do",
        "how is the token refreshed",
        "describe the approval service",
    ):
        assert _intent(q) == "explain_code", q


def test_repository_search_variants():
    for q in ("search for calculator", "search the repository for jwt"):
        assert _intent(q) == "repository_search", q


def test_unknown_question():
    result = detect_intent("greetings, friend")
    assert result.intent == "unknown"
    assert result.confidence == 0.1
    assert result.subject == ""
    assert result.matched_keywords == ()


def test_confidence_bounds():
    for q in (
        "Explain the dealer approval workflow",
        "Where is NotificationService?",
        "Review PR #1",
        "hello world",
    ):
        result = detect_intent(q)
        assert 0.0 <= result.confidence <= 0.99


def test_confidence_increases_with_matches():
    one = detect_intent("Explain the approval service")
    two = detect_intent("Explain the approval service architecture")
    assert two.confidence > one.confidence


def test_subject_strips_stopwords_and_keywords():
    result = detect_intent("Where is NotificationService?")
    assert result.subject == "notificationservice"


def test_subject_keeps_meaningful_words():
    result = detect_intent("Explain dealer approval workflow")
    assert result.subject == "dealer approval"


def test_subject_dedupes_repeats():
    result = detect_intent("Explain the approval and the approval again")
    assert result.subject.count("approval") == 1


def test_deterministic():
    q = "Generate an issue draft for the dealer approval crash"
    a, b = detect_intent(q), detect_intent(q)
    assert a == b


def test_case_and_punctuation_insensitive():
    assert _intent("REVIEW PR #1!") == "review_pr"
    assert _intent("Where is NotificationService?") == "find_implementation"

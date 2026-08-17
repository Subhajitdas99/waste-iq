"""Benchmark case registry — the authoritative evaluation suite.

Every case is deterministic and self-contained. ``mode="manual"`` cases
exercise behaviour the deterministic assistants do not produce yet (LLM
prose is deferred); they are scored by a human per ``docs/evaluation/
SCORING_GUIDE.md`` and reported separately.
"""

from __future__ import annotations

from app.evaluation.schema import BenchmarkCase

# ---------------------------------------------------------------------------
# Repository Search — does retrieval find the right file?
# ---------------------------------------------------------------------------

REPOSITORY_SEARCH_CASES: list[BenchmarkCase] = [
    BenchmarkCase(
        id="rs-01-find-notification-service",
        category="repository_search",
        question="Find NotificationService",
        expected_behaviour=(
            "The NotificationService class in backend/app/services/notifications.py "
            "must be returned in the top-5 results."
        ),
        expected_files=["backend/app/services/notifications.py"],
        payload={"search_query": "notification service backend"},
    ),
    BenchmarkCase(
        id="rs-02-find-marketplace-apis",
        category="repository_search",
        question="Find Marketplace APIs",
        expected_behaviour=(
            "The marketplace router with inventory reserve/purchase endpoints "
            "(backend/app/api/routes/marketplace.py) must be returned in the top-5."
        ),
        expected_files=["backend/app/api/routes/marketplace.py"],
        payload={"search_query": "marketplace reserve inventory backend"},
    ),
    BenchmarkCase(
        id="rs-03-find-review-engine",
        category="repository_search",
        question="Find review_engine",
        expected_behaviour=(
            "agent/app/review/review_engine.py (ReviewEngine) must be returned " "in the top-5."
        ),
        expected_files=["agent/app/review/review_engine.py"],
        payload={"search_query": "review engine implementation"},
    ),
    BenchmarkCase(
        id="rs-04-find-repository-indexer",
        category="repository_search",
        question="Find RepositoryIndexer",
        expected_behaviour=(
            "agent/app/context/repository_indexer.py (RepositoryIndexer) must be "
            "returned in the top-5."
        ),
        expected_files=["agent/app/context/repository_indexer.py"],
        payload={"search_query": "repository indexer"},
    ),
    BenchmarkCase(
        id="rs-05-find-jwt-service",
        category="repository_search",
        question="Find JWTService",
        expected_behaviour=(
            "JWT token helpers (create_access_token/decode_access_token in "
            "backend/app/core/security.py) must be returned in the top-5. "
            "No JWTService class exists; the actual implementation is a module."
        ),
        expected_files=["backend/app/core/security.py"],
        payload={"search_query": "JWT access token create"},
    ),
    BenchmarkCase(
        id="rs-06-explain-dealer-approval",
        category="repository_search",
        question="Explain Dealer Approval",
        expected_behaviour=(
            "The dealer approval workflow (backend/app/services/dealer_approval.py) "
            "must be returned in the top-5 with usable evidence."
        ),
        expected_files=["backend/app/services/dealer_approval.py"],
        payload={"search_query": "dealer approval workflow"},
    ),
]

# ---------------------------------------------------------------------------
# Architecture — does retrieval surface the right decisions?
# ---------------------------------------------------------------------------

ARCHITECTURE_CASES: list[BenchmarkCase] = [
    BenchmarkCase(
        id="ar-01-explain-adr-004",
        category="architecture",
        question="Explain ADR-004",
        expected_behaviour=(
            "ADR-004 (AI assistance is propose-only by default) must be found in "
            "ARCHITECTURE_DECISIONS.md with a usable explanation."
        ),
        expected_files=["docs/architecture/ARCHITECTURE_DECISIONS.md"],
        expected_adrs=["ADR-004"],
        payload={"search_query": "ADR-004 propose-only"},
    ),
    BenchmarkCase(
        id="ar-02-explain-adr-008",
        category="architecture",
        question="Explain ADR-008",
        expected_behaviour=(
            "ADR-008 (PR review is deterministic and evidence-backed first) must be "
            "found in ARCHITECTURE_DECISIONS.md."
        ),
        expected_files=["docs/architecture/ARCHITECTURE_DECISIONS.md"],
        expected_adrs=["ADR-008"],
        payload={"search_query": "ADR-008 review evidence-backed deterministic"},
    ),
    BenchmarkCase(
        id="ar-03-explain-repository-pattern",
        category="architecture",
        question="Explain Repository Pattern",
        expected_behaviour=(
            "The layered architecture decision (ADR-001: api/routes -> services -> "
            "repositories -> models) must be found, along with repository-layer "
            "implementation files."
        ),
        expected_files=[
            "docs/architecture/ARCHITECTURE_DECISIONS.md",
            "backend/app/repositories",
        ],
        expected_adrs=["ADR-001"],
        payload={
            "search_query": "backend layered architecture routes services repositories models"
        },
    ),
    BenchmarkCase(
        id="ar-04-explain-marketplace-architecture",
        category="architecture",
        question="Explain Marketplace Architecture",
        expected_behaviour=(
            "Marketplace architecture must be retrievable: the marketplace router, "
            "service, models, and the ADR covering feature modules."
        ),
        expected_files=[
            "backend/app/api/routes/marketplace.py",
            "backend/app/services/marketplace.py",
            "backend/app/models/marketplace_order.py",
        ],
        expected_adrs=["ADR-001"],
        payload={"search_query": "marketplace module router service order model"},
    ),
]

# ---------------------------------------------------------------------------
# Issue Assistant — triage quality
# ---------------------------------------------------------------------------

ISSUE_ASSISTANT_CASES: list[BenchmarkCase] = [
    BenchmarkCase(
        id="ia-01-generate-issue-draft",
        category="issue_assistant",
        question="Generate Issue Draft",
        expected_behaviour=(
            "Analyzing a new bug issue produces a triage: a priority (high or "
            "critical for a crash), bug/backend labels, and at least one evidence "
            "citation when the repository index is available."
        ),
        expected_files=["backend/app/services/dealer_approval.py"],
        expected_services=["IssueAssistant.analyze"],
        payload={
            "issue": {
                "number": 9001,
                "title": "Dealer approval stuck after failed dealer registration",
                "body": (
                    "When a dealer registers with invalid data the approval workflow "
                    "crashes with an exception and the approval record stays stuck forever."
                ),
            },
            "repo_labels": ["bug", "backend", "security", "enhancement"],
        },
    ),
    BenchmarkCase(
        id="ia-02-duplicate-detection",
        category="issue_assistant",
        question="Duplicate Detection",
        expected_behaviour=(
            "A nearly identical open issue must be flagged as a possible duplicate."
        ),
        expected_services=["IssueAssistant.analyze"],
        payload={
            "issue": {
                "number": 9002,
                "title": "Login API returns 500 on wrong password",
                "body": "Logging in with a wrong password crashes the server.",
            },
            "open_issues": [
                {
                    "number": 9003,
                    "title": "Login API broken on bad credentials",
                    "body": "Logging in with wrong password raises an exception.",
                },
                {"number": 9004, "title": "Add dark mode to dashboard", "body": "UI nicety."},
            ],
            "repo_labels": None,
        },
    ),
    BenchmarkCase(
        id="ia-03-label-suggestions",
        category="issue_assistant",
        question="Label Suggestions",
        expected_behaviour=(
            "Keyword rules produce label suggestions that are filtered to the "
            "repository's real labels only."
        ),
        expected_services=["IssueAssistant.analyze"],
        payload={
            "issue": {
                "number": 9005,
                "title": "Security vulnerability in auth",
                "body": "Potential XSS injection in login form.",
            },
            "repo_labels": ["bug", "security"],
        },
    ),
    BenchmarkCase(
        id="ia-04-milestone-suggestions",
        category="issue_assistant",
        question="Milestone Suggestions",
        expected_behaviour=(
            "When roadmap evidence (WIQ-V1-### / M# tokens) is retrieved, the "
            "milestone is suggested; otherwise milestone stays None and the "
            "triage still completes."
        ),
        expected_services=["IssueAssistant.analyze"],
        payload={
            "issue": {
                "number": 9006,
                "title": "Roadmap: WIQ-V1-003 issue assistant",
                "body": "Implement the issue assistant per the roadmap.",
            },
            "repo_labels": None,
        },
    ),
    BenchmarkCase(
        id="ia-05-acceptance-criteria",
        category="issue_assistant",
        mode="manual",
        question="Acceptance Criteria",
        expected_behaviour=(
            "The triage comment includes acceptance criteria for the issue "
            "(LLM-prose capability, deferred; scored manually)."
        ),
        expected_services=["IssueAssistant"],
    ),
    BenchmarkCase(
        id="ia-06-complexity-estimation",
        category="issue_assistant",
        mode="manual",
        question="Complexity Estimation",
        expected_behaviour=(
            "The triage estimates issue complexity (LLM-prose capability, deferred; "
            "scored manually)."
        ),
        expected_services=["IssueAssistant"],
    ),
]

# ---------------------------------------------------------------------------
# PR Review — does the review engine catch what it must?
# ---------------------------------------------------------------------------

PR_REVIEW_FILES = [
    "backend/app/routes/payments.py",
    "backend/app/routes/analytics.py",
    "backend/tests/test_payments.py",
    "frontend/src/components/PaymentList.jsx",
]

PR_REVIEW_CASES: list[BenchmarkCase] = [
    BenchmarkCase(
        id="pr-01-review-sample-pr",
        category="pr_review",
        question="Review Sample PR",
        expected_behaviour=(
            "Submitting the demo fixture PR completes with findings across "
            "categories and a summary."
        ),
        expected_files=PR_REVIEW_FILES,
        payload={"repository": "waste-iq/demo", "pr_number": 1},
    ),
    BenchmarkCase(
        id="pr-02-missing-tests",
        category="pr_review",
        question="Missing Tests",
        expected_behaviour=(
            "TEST-GAP fires for a changed backend file with no accompanying test "
            "change, and test-quality rules fire on the test file."
        ),
        expected_files=PR_REVIEW_FILES,
        expected_services=["TEST-GAP", "TEST-SKIP-NEW", "TEST-SLEEP"],
        payload={"repository": "waste-iq/demo", "pr_number": 1},
    ),
    BenchmarkCase(
        id="pr-03-security-findings",
        category="pr_review",
        question="Security Findings",
        expected_behaviour=(
            "Security rules fire on the changed code (SEC-EVAL on the analytics "
            "route at minimum)."
        ),
        expected_files=PR_REVIEW_FILES,
        expected_services=["SEC-EVAL"],
        payload={"repository": "waste-iq/demo", "pr_number": 1},
    ),
    BenchmarkCase(
        id="pr-04-architecture-findings",
        category="pr_review",
        question="Architecture Findings",
        expected_behaviour="ARCH-ROUTE-DB fires (direct DB access from a route handler).",
        expected_files=PR_REVIEW_FILES,
        expected_services=["ARCH-ROUTE-DB"],
        payload={"repository": "waste-iq/demo", "pr_number": 1},
    ),
    BenchmarkCase(
        id="pr-05-performance-findings",
        category="pr_review",
        question="Performance Findings",
        expected_behaviour="PERF-NPLUS fires (N+1 queries in a loop).",
        expected_files=PR_REVIEW_FILES,
        expected_services=["PERF-NPLUS"],
        payload={"repository": "waste-iq/demo", "pr_number": 1},
    ),
    BenchmarkCase(
        id="pr-06-evidence-validation",
        category="pr_review",
        question="Evidence Validation",
        expected_behaviour=(
            "Every finding cites a file that is part of the reviewed diff "
            "(no out-of-diff references); repository-context references resolve."
        ),
        expected_files=PR_REVIEW_FILES,
        payload={"repository": "waste-iq/demo", "pr_number": 1},
    ),
]

# ---------------------------------------------------------------------------
# Documentation Agent — changelog + drift
# ---------------------------------------------------------------------------

DOCUMENTATION_CASES: list[BenchmarkCase] = [
    BenchmarkCase(
        id="dc-01-generate-changelog",
        category="documentation",
        question="Generate Changelog",
        expected_behaviour=(
            "A conventional-commit title maps to a Keep a Changelog section and a "
            "well-formed entry referencing the PR number."
        ),
        expected_services=["build_changelog_entry"],
        payload={"pr_title": "feat(api): add notifications endpoint", "pr_number": 42},
    ),
    BenchmarkCase(
        id="dc-02-summarize-pull-request",
        category="documentation",
        question="Summarize Pull Request",
        expected_behaviour=(
            "Analyzing a merged PR produces a proposal whose summary names the PR "
            "and lists the generated changelog/doc actions."
        ),
        expected_services=["DocAssistant.analyze"],
        payload={
            "pr_title": "feat(api): add notifications endpoint",
            "pr_number": 42,
            "changed_files": ["backend/app/api/routes/notifications.py"],
        },
    ),
    BenchmarkCase(
        id="dc-03-explain-module",
        category="documentation",
        question="Explain Module",
        expected_behaviour=(
            "The NotificationService module is retrievable with evidence "
            "sufficient to explain it."
        ),
        expected_files=["backend/app/services/notifications.py"],
        payload={"search_query": "notification service backend"},
    ),
    BenchmarkCase(
        id="dc-04-generate-api-documentation",
        category="documentation",
        question="Generate API Documentation",
        expected_behaviour=(
            "A PR touching API routes produces a doc update suggestion for "
            "docs/API_SPECIFICATION.md."
        ),
        expected_files=["docs/API_SPECIFICATION.md"],
        expected_services=["DocAssistant.analyze"],
        payload={
            "pr_title": "feat(api): add notifications endpoint",
            "pr_number": 42,
            "changed_files": [
                "backend/app/api/routes/notifications.py",
                "backend/app/schemas/notifications.py",
            ],
        },
    ),
    BenchmarkCase(
        id="dc-05-detect-documentation-drift",
        category="documentation",
        question="Detect Documentation Drift",
        expected_behaviour=(
            "A PR changing models produces a doc update suggestion for "
            "docs/DATABASE_SCHEMA.md; a PR changing only docs produces no "
            "suggestions."
        ),
        expected_files=["docs/DATABASE_SCHEMA.md"],
        expected_services=["DocAssistant.analyze"],
        payload={
            "pr_title": "feat(models): add pickup table",
            "pr_number": 43,
            "changed_files": [
                "backend/app/models/pickup.py",
                "backend/app/repositories/pickups.py",
            ],
        },
    ),
]

# ---------------------------------------------------------------------------
# LLM Layer — grounding, prompts, parsing, cache, telemetry, providers
# ---------------------------------------------------------------------------

LLM_LAYER_CASES: list[BenchmarkCase] = [
    BenchmarkCase(
        id="ll-01-grounding-validation",
        category="llm_layer",
        question="Grounding Validation",
        expected_behaviour=(
            "An LLM response whose claims all reference provided evidence passes "
            "grounding validation."
        ),
        expected_services=["build_evidence_entries", "validate"],
        payload={"check": "grounding_validation"},
    ),
    BenchmarkCase(
        id="ll-02-prompt-quality",
        category="llm_layer",
        question="Prompt Quality",
        expected_behaviour=(
            "PromptBuilder builds system + user prompts that embed the evidence and "
            "redact secrets."
        ),
        expected_services=["PromptBuilder.build", "Redactor.redact"],
        payload={"check": "prompt_quality"},
    ),
    BenchmarkCase(
        id="ll-03-json-validation",
        category="llm_layer",
        question="JSON Validation",
        expected_behaviour=(
            "Fenced JSON from model output parses into the role's response model; "
            "malformed output raises MalformedResponseError."
        ),
        expected_services=["extract_json", "ResponseParser.parse"],
        payload={"check": "json_validation"},
    ),
    BenchmarkCase(
        id="ll-04-cache-validation",
        category="llm_layer",
        question="Cache Validation",
        expected_behaviour=(
            "Identical requests hash identically and the cache backend stores and "
            "returns hits deterministically."
        ),
        expected_services=["hash_request", "MemoryCache"],
        payload={"check": "cache_validation"},
    ),
    BenchmarkCase(
        id="ll-05-telemetry",
        category="llm_layer",
        question="Telemetry",
        expected_behaviour=(
            "Recorded calls and cache events are reflected in the telemetry " "snapshot."
        ),
        expected_services=["Telemetry.record_call", "Telemetry.snapshot"],
        payload={"check": "telemetry"},
    ),
    BenchmarkCase(
        id="ll-06-provider-selection",
        category="llm_layer",
        question="Provider Selection",
        expected_behaviour=(
            "Without cloud credentials the provider resolver selects the "
            "deterministic mock provider."
        ),
        expected_services=["resolve_provider", "build_provider", "MockProvider"],
        payload={"check": "provider_selection"},
    ),
    BenchmarkCase(
        id="ll-07-hallucination-rejection",
        category="llm_layer",
        question="Hallucination Rejection",
        expected_behaviour=(
            "An LLM response with a claim outside the evidence universe is "
            "rejected with GroundingViolationError — hallucination must never "
            "reach the caller."
        ),
        expected_services=["validate", "GroundingViolationError"],
        payload={"check": "hallucination_rejection"},
    ),
]

BENCHMARK_CASES: list[BenchmarkCase] = (
    REPOSITORY_SEARCH_CASES
    + ARCHITECTURE_CASES
    + ISSUE_ASSISTANT_CASES
    + PR_REVIEW_CASES
    + DOCUMENTATION_CASES
    + LLM_LAYER_CASES
)

CATEGORY_ORDER = [
    "repository_search",
    "architecture",
    "issue_assistant",
    "pr_review",
    "documentation",
    "llm_layer",
]

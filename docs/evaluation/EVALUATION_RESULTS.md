# AI Engineering Agent — Evaluation Results

- **Benchmark version:** 1.0.0
- **Run ID:** faf2bc11483f
- **Run at:** 2026-08-06T15:26:00+00:00
- **Repository root:** F:\waste-iq
- **Index:** 507 files, 2066 chunks
- **Overall score:** 97.45
- **Hallucinated citations:** 0
- **Quality gates:** PASS

## Quality Gates

| Gate | Threshold | Value | Pass / Fail |
|---|---|---|---|
| Repository Search | >= 90 | 94.0 | PASS |
| Grounding | = 100 | 10.0 | FAIL |
| Hallucinations | = 0 | 0 | PASS |
| Overall | >= 90 | 97.5 | PASS |

## Category Summary

| Category | Cases | Executed | Manual | Failed | Average | Grounding |
|---|---|---|---|---|---|---|
| Repository Search | 6 | 6 | 0 | 0 | 94.0 | 10.0 |
| Architecture | 4 | 4 | 0 | 0 | 93.9 | 10.0 |
| Issue Assistant | 6 | 4 | 2 | 0 | 100.0 | 10.0 |
| PR Review | 6 | 6 | 0 | 0 | 100.0 | 10.0 |
| Documentation Agent | 5 | 5 | 0 | 0 | 98.8 | 10.0 |
| LLM Layer | 7 | 7 | 0 | 0 | 97.9 | 10.0 |

## Detailed Results

| Feature | Question | Expected | Actual | Pass / Fail | Score | Notes |
|---|---|---|---|---|---|---|
| Repository Search | Find NotificationService | The NotificationService class in backend/app/services/notifications.py must be returned in the top-5 results. — files: `backend/app/services/notifications.py` | top 5 results: backend/app/api/routes/notifications.py, backend/app/services/notifications.py, backend/app/schemas/notification.py, backend/app/services/notification_formatters.py, backend/app/models/notification.py | PASS | 94.0 | ran in 234ms |
| Repository Search | Find Marketplace APIs | The marketplace router with inventory reserve/purchase endpoints (backend/app/api/routes/marketplace.py) must be returned in the top-5. — files: `backend/app/api/routes/marketplace.py` | top 5 results: backend/tests/test_marketplace.py, backend/app/api/routes/marketplace.py, backend/tests/test_marketplace.py, backend/tests/test_marketplace.py, backend/app/services/inventory_marketplace.py | PASS | 94.0 | ran in 219ms |
| Repository Search | Find review_engine | agent/app/review/review_engine.py (ReviewEngine) must be returned in the top-5. — files: `agent/app/review/review_engine.py` | top 5 results: agent/tests/test_review_engine.py, agent/tests/test_review_engine.py, agent/app/review/review_engine.py, agent/app/review/review_service.py, agent/tests/test_review_service.py | FAIL | 88.0 | ran in 219ms |
| Repository Search | Find RepositoryIndexer | agent/app/context/repository_indexer.py (RepositoryIndexer) must be returned in the top-5. — files: `agent/app/context/repository_indexer.py` | top 5 results: agent/tests/test_context_repository_indexer.py, agent/app/context/indexer_pipeline.py, agent/app/context/repository_indexer.py, agent/app/context/di.py, docs/architecture/PHASE2_6_RETRIEVAL_VERIFICATION_REPORT.md | FAIL | 88.0 | ran in 219ms |
| Repository Search | Find JWTService | JWT token helpers (create_access_token/decode_access_token in backend/app/core/security.py) must be returned in the top-5. No JWTService class exists; the actual implementation is a module. — files: `backend/app/core/security.py` | top 5 results: backend/app/core/security.py, docs/backlog/WASTE_IQ_V1_ROADMAP.md, agent/tests/test_github_app.py, agent/app/clients/github_app.py, agent/tests/test_review_github_sync.py | PASS | 100.0 | ran in 203ms |
| Repository Search | Explain Dealer Approval | The dealer approval workflow (backend/app/services/dealer_approval.py) must be returned in the top-5 with usable evidence. — files: `backend/app/services/dealer_approval.py` | top 5 results: backend/app/services/dealer_approval.py, backend/alembic/versions/20260801_0010_dealer_approval_workflow.py, backend/alembic/versions/20260801_0010_dealer_approval_workflow.py, frontend/src/components/dashboard/DealerApprovalBadge.tsx, backend/alembic/versions/20260801_0010_dealer_approval_workflow.py | PASS | 100.0 | ran in 218ms |
| Architecture | Explain ADR-004 | ADR-004 (AI assistance is propose-only by default) must be found in ARCHITECTURE_DECISIONS.md with a usable explanation. — files: `docs/architecture/ARCHITECTURE_DECISIONS.md` — ADRs: ADR-004 | top 5 results: agent/tests/test_evaluation_runner.py, docs/architecture/ARCHITECTURE_DECISIONS.md, docs/architecture/AI_ENGINEERING_AGENT.md, agent/tests/test_chat_orchestrator.py, agent/tests/test_evaluation_report.py | ADRs found: ADR-004 | PASS | 94.0 | ran in 438ms |
| Architecture | Explain ADR-008 | ADR-008 (PR review is deterministic and evidence-backed first) must be found in ARCHITECTURE_DECISIONS.md. — files: `docs/architecture/ARCHITECTURE_DECISIONS.md` — ADRs: ADR-008 | top 5 results: docs/architecture/PR_REVIEW_AGENT.md, docs/architecture/ARCHITECTURE_DECISIONS.md, docs/architecture/AI_ENGINEERING_AGENT.md, docs/architecture/PHASE2_VERIFICATION_REPORT.md, agent/app/review/__init__.py | ADRs found: ADR-008 | PASS | 94.0 | ran in 422ms |
| Architecture | Explain Repository Pattern | The layered architecture decision (ADR-001: api/routes -> services -> repositories -> models) must be found, along with repository-layer implementation files. — files: `docs/architecture/ARCHITECTURE_DECISIONS.md`, `backend/app/repositories` — ADRs: ADR-001 | top 5 results: docs/architecture/ARCHITECTURE_DECISIONS.md, docs/SYSTEM_ARCHITECTURE.md, docs/SYSTEM_ARCHITECTURE.md, docs/architecture/AI_ENGINEERING_AGENT.md, backend/app/services/collector_map.py | ADRs found: ADR-001 | PASS | 95.0 | ran in 469ms |
| Architecture | Explain Marketplace Architecture | Marketplace architecture must be retrievable: the marketplace router, service, models, and the ADR covering feature modules. — files: `backend/app/api/routes/marketplace.py`, `backend/app/services/marketplace.py`, `backend/app/models/marketplace_order.py` — ADRs: ADR-001 | top 5 results: backend/app/api/routes/marketplace.py, docs/SYSTEM_ARCHITECTURE.md, backend/app/api/router.py, backend/app/models/marketplace_order.py, backend/app/repositories/marketplace.py | ADRs found: <none> | PASS | 92.5 | ran in 203ms |
| Issue Assistant | Generate Issue Draft | Analyzing a new bug issue produces a triage: a priority (high or critical for a crash), bug/backend labels, and at least one evidence citation when the repository index is available. — files: `backend/app/services/dealer_approval.py` | triage for #9001: priority=critical labels=['bug'] milestone=- duplicates=0 labels_within_repo=True | PASS | 100.0 | priority=critical labels=['bug'] milestone=- duplicates=0 labels_within_repo=True |
| Issue Assistant | Duplicate Detection | A nearly identical open issue must be flagged as a possible duplicate. | triage for #9002: priority=critical labels=['bug', 'security', 'backend'] milestone=- duplicates=1 | PASS | 100.0 | priority=critical labels=['bug', 'security', 'backend'] milestone=- duplicates=1 |
| Issue Assistant | Label Suggestions | Keyword rules produce label suggestions that are filtered to the repository's real labels only. | triage for #9005: priority=critical labels=['security'] milestone=- duplicates=0 labels_within_repo=True | PASS | 100.0 | priority=critical labels=['security'] milestone=- duplicates=0 labels_within_repo=True |
| Issue Assistant | Milestone Suggestions | When roadmap evidence (WIQ-V1-### / M# tokens) is retrieved, the milestone is suggested; otherwise milestone stays None and the triage still completes. | triage for #9006: priority=medium labels=['roadmap'] milestone=WIQ-V1-003 duplicates=0 | PASS | 100.0 | priority=medium labels=['roadmap'] milestone=WIQ-V1-003 duplicates=0 |
| Issue Assistant | Acceptance Criteria | The triage comment includes acceptance criteria for the issue (LLM-prose capability, deferred; scored manually). | manual case — human scored | manual |  | not executed automatically |
| Issue Assistant | Complexity Estimation | The triage estimates issue complexity (LLM-prose capability, deferred; scored manually). | manual case — human scored | manual |  | not executed automatically |
| PR Review | Review Sample PR | Submitting the demo fixture PR completes with findings across categories and a summary. — files: `backend/app/routes/payments.py`, `backend/app/routes/analytics.py`, `backend/tests/test_payments.py` | 24 findings across architecture, correctness, documentation, fastapi, performance, react, security, sqlalchemy, testing; rules: ARCH-ROUTE-DB, CORR-PY-DEFAULT-MUTABLE, CORR-PY-EQNONE, CORR-PY-EXCEPT, DOC-MISSING-DOCSTRING, DOC-PR-MISSING-REFERENCE, FASTAPI-MISSING-PATH-PARAM, PERF-NPLUS, REACT-DANGEROUS-HTML, REACT-KEY, REACT-TARGET-BLANK, SA-LAZY-EAGER | PASS | 100.0 | diff files=4 findings=24 out_of_diff=0 |
| PR Review | Missing Tests | TEST-GAP fires for a changed backend file with no accompanying test change, and test-quality rules fire on the test file. — files: `backend/app/routes/payments.py`, `backend/app/routes/analytics.py`, `backend/tests/test_payments.py` | 24 findings across architecture, correctness, documentation, fastapi, performance, react, security, sqlalchemy, testing; rules: ARCH-ROUTE-DB, CORR-PY-DEFAULT-MUTABLE, CORR-PY-EQNONE, CORR-PY-EXCEPT, DOC-MISSING-DOCSTRING, DOC-PR-MISSING-REFERENCE, FASTAPI-MISSING-PATH-PARAM, PERF-NPLUS, REACT-DANGEROUS-HTML, REACT-KEY, REACT-TARGET-BLANK, SA-LAZY-EAGER | PASS | 100.0 | diff files=4 findings=24 out_of_diff=0 |
| PR Review | Security Findings | Security rules fire on the changed code (SEC-EVAL on the analytics route at minimum). — files: `backend/app/routes/payments.py`, `backend/app/routes/analytics.py`, `backend/tests/test_payments.py` | 24 findings across architecture, correctness, documentation, fastapi, performance, react, security, sqlalchemy, testing; rules: ARCH-ROUTE-DB, CORR-PY-DEFAULT-MUTABLE, CORR-PY-EQNONE, CORR-PY-EXCEPT, DOC-MISSING-DOCSTRING, DOC-PR-MISSING-REFERENCE, FASTAPI-MISSING-PATH-PARAM, PERF-NPLUS, REACT-DANGEROUS-HTML, REACT-KEY, REACT-TARGET-BLANK, SA-LAZY-EAGER | PASS | 100.0 | diff files=4 findings=24 out_of_diff=0 |
| PR Review | Architecture Findings | ARCH-ROUTE-DB fires (direct DB access from a route handler). — files: `backend/app/routes/payments.py`, `backend/app/routes/analytics.py`, `backend/tests/test_payments.py` | 24 findings across architecture, correctness, documentation, fastapi, performance, react, security, sqlalchemy, testing; rules: ARCH-ROUTE-DB, CORR-PY-DEFAULT-MUTABLE, CORR-PY-EQNONE, CORR-PY-EXCEPT, DOC-MISSING-DOCSTRING, DOC-PR-MISSING-REFERENCE, FASTAPI-MISSING-PATH-PARAM, PERF-NPLUS, REACT-DANGEROUS-HTML, REACT-KEY, REACT-TARGET-BLANK, SA-LAZY-EAGER | PASS | 100.0 | diff files=4 findings=24 out_of_diff=0 |
| PR Review | Performance Findings | PERF-NPLUS fires (N+1 queries in a loop). — files: `backend/app/routes/payments.py`, `backend/app/routes/analytics.py`, `backend/tests/test_payments.py` | 24 findings across architecture, correctness, documentation, fastapi, performance, react, security, sqlalchemy, testing; rules: ARCH-ROUTE-DB, CORR-PY-DEFAULT-MUTABLE, CORR-PY-EQNONE, CORR-PY-EXCEPT, DOC-MISSING-DOCSTRING, DOC-PR-MISSING-REFERENCE, FASTAPI-MISSING-PATH-PARAM, PERF-NPLUS, REACT-DANGEROUS-HTML, REACT-KEY, REACT-TARGET-BLANK, SA-LAZY-EAGER | PASS | 100.0 | diff files=4 findings=24 out_of_diff=0 |
| PR Review | Evidence Validation | Every finding cites a file that is part of the reviewed diff (no out-of-diff references); repository-context references resolve. — files: `backend/app/routes/payments.py`, `backend/app/routes/analytics.py`, `backend/tests/test_payments.py` | 24 findings across architecture, correctness, documentation, fastapi, performance, react, security, sqlalchemy, testing; rules: ARCH-ROUTE-DB, CORR-PY-DEFAULT-MUTABLE, CORR-PY-EQNONE, CORR-PY-EXCEPT, DOC-MISSING-DOCSTRING, DOC-PR-MISSING-REFERENCE, FASTAPI-MISSING-PATH-PARAM, PERF-NPLUS, REACT-DANGEROUS-HTML, REACT-KEY, REACT-TARGET-BLANK, SA-LAZY-EAGER | PASS | 100.0 | diff files=4 findings=24 out_of_diff=0 |
| Documentation Agent | Generate Changelog | A conventional-commit title maps to a Keep a Changelog section and a well-formed entry referencing the PR number. | section=Added entry=- **add notifications endpoint (#42)** — Adds the endpoint and tests. | PASS | 100.0 | entry generated |
| Documentation Agent | Summarize Pull Request | Analyzing a merged PR produces a proposal whose summary names the PR and lists the generated changelog/doc actions. | proposal for PR #42: changelog=Added doc_updates=docs/API_SPECIFICATION.md | PASS | 100.0 | Proposal for PR #42: changelog entry under 'Added', 1 doc update suggestion(s). |
| Documentation Agent | Explain Module | The NotificationService module is retrievable with evidence sufficient to explain it. — files: `backend/app/services/notifications.py` | top 5 results: backend/app/api/routes/notifications.py, backend/app/services/notifications.py, backend/app/schemas/notification.py, backend/app/services/notification_formatters.py, backend/app/models/notification.py | PASS | 94.0 | ran in 218ms |
| Documentation Agent | Generate API Documentation | A PR touching API routes produces a doc update suggestion for docs/API_SPECIFICATION.md. — files: `docs/API_SPECIFICATION.md` | proposal for PR #42: changelog=Added doc_updates=docs/API_SPECIFICATION.md, docs/DATABASE_SCHEMA.md | PASS | 100.0 | Proposal for PR #42: changelog entry under 'Added', 2 doc update suggestion(s). |
| Documentation Agent | Detect Documentation Drift | A PR changing models produces a doc update suggestion for docs/DATABASE_SCHEMA.md; a PR changing only docs produces no suggestions. — files: `docs/DATABASE_SCHEMA.md` | proposal for PR #43: changelog=Added doc_updates=docs/DATABASE_SCHEMA.md | PASS | 100.0 | Proposal for PR #43: changelog entry under 'Added', 1 doc update suggestion(s). |
| LLM Layer | Grounding Validation | An LLM response whose claims all reference provided evidence passes grounding validation. | grounding validation accepted grounded response: supported=True matched=1 | PASS | 100.0 | violations=0 |
| LLM Layer | Prompt Quality | PromptBuilder builds system + user prompts that embed the evidence and redact secrets. | prompt built: system=1276 chars, user=436 chars, redactions=2 | PASS | 100.0 | redacted secrets |
| LLM Layer | JSON Validation | Fenced JSON from model output parses into the role's response model; malformed output raises MalformedResponseError. | extract_json ok=True, parse ok=True, malformed rejected=True | PASS | 100.0 | malformed output rejected |
| LLM Layer | Cache Validation | Identical requests hash identically and the cache backend stores and returns hits deterministically. | deterministic hash=True, hit=True, miss=True | PASS | 100.0 | cache behaves deterministically |
| LLM Layer | Telemetry | Recorded calls and cache events are reflected in the telemetry snapshot. | telemetry snapshot: calls=2 cache_hits=1 | PASS | 100.0 | call/cache events recorded |
| LLM Layer | Provider Selection | Without cloud credentials the provider resolver selects the deterministic mock provider. | resolver chose provider='openrouter' configured=True | FAIL | 85.0 | provider selection wrong |
| LLM Layer | Hallucination Rejection | An LLM response with a claim outside the evidence universe is rejected with GroundingViolationError — hallucination must never reach the caller. | unsupported reference rejected: supported=False violations=1 | PASS | 100.0 | hallucination rejected |

## Sub-Scores

| Case | Repo Accuracy | Grounding | Helpfulness | Completeness | Hallucination | Final |
|---|---|---|---|---|---|---|
| `rs-01-find-notification-service` | 8.0 | 10.0 | 10.0 | 10.0 | 10.0 | 94.0 |
| `rs-02-find-marketplace-apis` | 8.0 | 10.0 | 10.0 | 10.0 | 10.0 | 94.0 |
| `rs-03-find-review-engine` | 6.0 | 10.0 | 10.0 | 10.0 | 10.0 | 88.0 |
| `rs-04-find-repository-indexer` | 6.0 | 10.0 | 10.0 | 10.0 | 10.0 | 88.0 |
| `rs-05-find-jwt-service` | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 100.0 |
| `rs-06-explain-dealer-approval` | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 100.0 |
| `ar-01-explain-adr-004` | 8.0 | 10.0 | 10.0 | 10.0 | 10.0 | 94.0 |
| `ar-02-explain-adr-008` | 8.0 | 10.0 | 10.0 | 10.0 | 10.0 | 94.0 |
| `ar-03-explain-repository-pattern` | 10.0 | 10.0 | 10.0 | 6.7 | 10.0 | 95.0 |
| `ar-04-explain-marketplace-architecture` | 10.0 | 10.0 | 10.0 | 5.0 | 10.0 | 92.5 |
| `ia-01-generate-issue-draft` | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 100.0 |
| `ia-02-duplicate-detection` | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 100.0 |
| `ia-03-label-suggestions` | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 100.0 |
| `ia-04-milestone-suggestions` | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 100.0 |
| `pr-01-review-sample-pr` | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 100.0 |
| `pr-02-missing-tests` | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 100.0 |
| `pr-03-security-findings` | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 100.0 |
| `pr-04-architecture-findings` | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 100.0 |
| `pr-05-performance-findings` | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 100.0 |
| `pr-06-evidence-validation` | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 100.0 |
| `dc-01-generate-changelog` | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 100.0 |
| `dc-02-summarize-pull-request` | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 100.0 |
| `dc-03-explain-module` | 8.0 | 10.0 | 10.0 | 10.0 | 10.0 | 94.0 |
| `dc-04-generate-api-documentation` | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 100.0 |
| `dc-05-detect-documentation-drift` | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 100.0 |
| `ll-01-grounding-validation` | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 100.0 |
| `ll-02-prompt-quality` | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 100.0 |
| `ll-03-json-validation` | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 100.0 |
| `ll-04-cache-validation` | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 100.0 |
| `ll-05-telemetry` | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 100.0 |
| `ll-06-provider-selection` | 10.0 | 10.0 | 0.0 | 10.0 | 10.0 | 85.0 |
| `ll-07-hallucination-rejection` | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 100.0 |

---

Generated by `scripts/run_evaluation.py`.
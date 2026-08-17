# Expected Results

Reference scores for a healthy agent at benchmark version 1.0.0 against the
current repository state. The automated regression comparison
(`run_evaluation.py --baseline`) uses a tolerance of 1.0 point per case and
flags any pass→fail flip.

These are *minimum* expectations, not aspirations: a case scoring below its
reference by more than the tolerance is a regression.

## Quality gates

| Gate | Threshold | Healthy value |
|---|---|---|
| Repository Search | ≥ 90 | 94.0 |
| Grounding | = 100 | 10.0 (100% of citations resolve) |
| Hallucinations | = 0 | 0 |
| Overall | ≥ 90 | 98.1 |

## Per-case reference scores

| Case | Expected final | Notes |
|---|---|---|
| rs-01 find-notification-service | ≥ 90 (94) | file at rank ≤ 2 |
| rs-02 find-marketplace-apis | ≥ 90 (94) | file at rank ≤ 2 |
| rs-03 find-review-engine | ≥ 85 (88) | test file dominates; implementation at rank 2-3 |
| rs-04 find-repository-indexer | ≥ 85 (88) | same token-density effect |
| rs-05 find-jwt-service | 100 | file at rank 1 |
| rs-06 explain-dealer-approval | 100 | file at rank 1 |
| ar-01 explain-adr-004 | ≥ 95 (100) | ADR found in top-5 |
| ar-02 explain-adr-008 | ≥ 90 (94) | ADR found at rank ≤ 2 |
| ar-03 explain-repository-pattern | ≥ 90 (95) | ADR + repo-layer file in top-5 |
| ar-04 explain-marketplace-architecture | ≥ 90 (92.5) | marketplace files at ranks 0-4; ADR-001 not always surfaced |
| ia-01 generate-issue-draft | 100 | crash triage + evidence |
| ia-02 duplicate-detection | 100 | |
| ia-03 label-suggestions | 100 | |
| ia-04 milestone-suggestions | 100 | |
| pr-01 review-sample-pr | 100 | |
| pr-02 missing-tests | 100 | |
| pr-03 security-findings | 100 | |
| pr-04 architecture-findings | 100 | |
| pr-05 performance-findings | 100 | |
| pr-06 evidence-validation | 100 | |
| dc-01 generate-changelog | 100 | |
| dc-02 summarize-pull-request | 100 | |
| dc-03 explain-module | ≥ 90 (94) | same retrieval as rs-01 |
| dc-04 generate-api-documentation | 100 | |
| dc-05 detect-documentation-drift | 100 | |
| ll-01..ll-07 | 100 | deterministic checks |

Manual cases (`ia-05`, `ia-06`) have no automated reference; score them per
`SCORING_GUIDE.md`.

## Category averages (healthy)

| Category | Average |
|---|---|
| Repository Search | ≥ 90 (94.0) |
| Architecture | ≥ 90 (95.4) |
| Issue Assistant | ≥ 90 (100.0, automated cases) |
| PR Review | 100.0 |
| Documentation Agent | ≥ 90 (98.8) |
| LLM Layer | 100.0 |
| **Overall** | **≥ 90 (98.1)** |

## Caveats

- `rs-03`/`rs-04`: the hybrid search's per-chunk sum scoring favours
  token-dense files, so the class under test usually ranks below its test
  suite. The expected file must still appear in the top-5; rank-based
  scores of 6 are the healthy baseline (see KNOWN_LIMITATIONS.md).
- `ar-04`: `docs/SYSTEM_ARCHITECTURE.md` legitimately competes with the
  marketplace files for rank 1; the case passes as long as the files are
  in the top-5.
- Scores are index-sensitive: adding/chunking docs shifts ranks slightly.
  Tolerances absorb that; compare against a baseline generated from the
  same repository state when investigating small deltas.

# Known Limitations

Honest documentation of what the benchmark does and does not measure, and
of the agent deficits it currently tolerates.

## Benchmark-level limitations

### 1. Per-chunk sum scoring favours token-dense files
`rs-03` and `rs-04` measure a real retrieval bias documented since
Phase 2.6: hybrid search scores are summed over keyword matches per chunk,
so large, token-dense files (test suites, generated docs) outrank small
class-definition chunks. For class-name queries the implementation file
typically ranks 2-3 behind its own test file. The benchmark calibrates
against this honestly (expected rank ≤ 5, healthy score 88) instead of
hiding it. Fixing the bias belongs to a retrieval phase, not the
benchmark.

### 2. The harness excludes itself from the corpus
`agent/app/evaluation/` and `docs/evaluation/` are ignored by the indexer.
The benchmark must not measure itself: case text and result reports
contain ADR ids, file paths and queries that would otherwise outrank the
real answers. This does mean the agent's searchable corpus differs from a
developer-facing index (by 8 files).

### 3. Index-state sensitivity
Scores depend on the current chunking of the repository (a doc rewrite
shifts ranks). The regression tolerance (1.0 point) and `--baseline`
comparison absorb this, but cross-state score comparisons are only valid
after re-indexing on the same tree.

### 4. In-memory vector store is per-process
The Phase 1 store rebuilds from SQLite on every pipeline run. A fresh
process has an empty store, so `--skip-index` is only meaningful with a
persistent store (qdrant/pgvector); the runner detects the empty case and
indexes anyway.

### 5. Manual cases are not automated
`ia-05` (acceptance criteria) and `ia-06` (complexity estimation) require
LLM prose the deterministic assistant does not produce yet. They are
human-scored (SCORING_GUIDE.md) and excluded from the gates. Until a
prose-capable assistant lands, the Issue Assistant category average
cannot exceed the automated cases.

### 6. Retrieval is not hallucination-proof
The grounding gate is only as strong as the corpus: a claim about a file
that exists but is *wrong* scores as grounded. The benchmark detects
non-existent citations, not semantic errors (that is the Review Agent's
job, and it is covered by pr-06 within the diff scope).

## Agent-level gaps the benchmark surfaces (not fixed by design)

| Gap | Evidence | Consequence |
|---|---|---|
| Class-name search rank bias | rs-03, rs-04 at 88 (rank 2-3) | Top-5 always contains the right file; the top hit is often the test suite |
| Architecture docs compete with dense system docs | ar-04 | ADR lookups can land below `SYSTEM_ARCHITECTURE.md` |
| Search query sensitivity | rs-01/dc-03 pass with natural phrasing, fail with bare class names | Users must include context words ("backend", "service") for the best results |

## What the benchmark deliberately does NOT test

- LLM prose quality (no LLM calls in the benchmark at all — deterministic
  by design).
- GitHub integration (webhooks, comments, patch PRs): covered by unit
  tests, not the benchmark.
- Human-judgement aspects of triage (priority *correctness* is asserted
  only for the crash scenario; other priorities are captured as text, not
  asserted).
- Performance/scale of indexing or search (timing is recorded in notes).

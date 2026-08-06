# AI Engineering Agent Benchmark

Deterministic, offline evaluation suite for the six agent capabilities.
One command, one score, four quality gates.

```bash
python scripts/run_evaluation.py
```

Exits `0` only when every quality gate passes. Results are written to
`docs/evaluation/EVALUATION_RESULTS.md`, the machine-readable state to
`agent/evaluation_state.json` (exposed by `GET /api/evaluation/status`).

## What it measures

| Category | Cases | What is verified |
|---|---|---|
| Repository Search | 6 | Class/API lookups return the right file in the top-5 |
| Architecture | 4 | ADR + architecture documents are retrievable |
| Issue Assistant | 6 (2 manual) | Triage priority, labels, duplicates, milestone, evidence |
| PR Review | 6 | Deterministic rule engine catches test/security/architecture/performance issues |
| Documentation Agent | 5 | Changelog entries, PR proposals, doc drift suggestions |
| LLM Layer | 7 | Grounding, prompts, JSON parsing, cache, telemetry, provider selection |

34 cases total (32 automated, 2 manual). See `TEST_CASES.md` for the full
registry and `EXPECTED_RESULTS.md` for what a healthy agent scores.

## Scoring

Every case yields five sub-scores (0-10) and a weighted final score (0-100):

| Sub-score | Weight | Meaning |
|---|---|---|
| Repository Accuracy | 0.30 | Did the answer find/reference the right files? Rank 1 = 10, rank 5 = 2 |
| Grounding | 0.25 | Do all citations resolve to real indexed files? |
| Helpfulness | 0.15 | Is the answer present, substantive, and does it meet the expected behaviour? |
| Completeness | 0.15 | Share of expected files/ADRs/services present |
| Hallucination Resistance | 0.15 | Zero non-existent citations |

A case passes at a final score of 90. `final = 10 × Σ(weight × subscore)`.

## Quality gates

| Gate | Threshold | Meaning |
|---|---|---|
| Repository Search | ≥ 90 | Average final score of the 6 search cases |
| Grounding | = 100 | Every executed case's citations resolve to indexed files |
| Hallucinations | = 0 | No cited file lies outside the indexed corpus |
| Overall | ≥ 90 | Average final score across all executed cases |

## Regression detection

```bash
python scripts/run_evaluation.py --baseline docs/evaluation/EVALUATION_RESULTS.json
```

Compares against a previous run's JSON and exits non-zero when any case
regresses by more than one point or flips from pass to fail. A baseline is
produced with `--json-output`:

```bash
python scripts/run_evaluation.py --json-output docs/evaluation/EVALUATION_RESULTS.json
```

## Operation notes

- The run always indexes first (`--skip-index` is safe only when a
  persistent vector store is configured; the in-memory store is rebuilt
  per process and the script re-indexes automatically when empty).
- The benchmark harness excludes itself from the indexed corpus
  (`agent/app/evaluation/`, `docs/evaluation/` are ignored dirs), so the
  agent is never measured against its own benchmark output.
- Manual cases (`ia-05`, `ia-06`) are scored by a human per `SCORING_GUIDE.md`;
  they do not affect the automated gates.
- The status endpoint `/api/evaluation/status` returns the last run's
  score, gates, and weakest/strongest category without re-running anything.

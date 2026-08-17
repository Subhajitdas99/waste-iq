# Scoring Guide

How every sub-score is computed, how to read the results, and how to score
the manual cases. The implementation lives in
`agent/app/evaluation/scoring.py`; this guide is the contract.

## The five sub-scores (0-10 each)

### Repository Accuracy — did the answer find the right files?
- Every case declares `expected_files` (path fragments).
- The best rank of any expected file among the cited files is mapped:
  rank 1 → 10, 2 → 8, 3 → 6, 4 → 4, 5 → 2, not found → 0.
- Cases with no file expectations (pure behaviour cases) score 10
  automatically when executed.
- *Read it as*: how close the retrieval got to the right answer, not just
  whether it appeared.

### Grounding — do the citations resolve?
- Every cited file must exist in the indexed corpus.
- 10 if all citations resolve (or none were produced), 0 if any citation
  is ungrounded.
- The quality gate requires the average to be exactly 10 across all
  executed cases — a single ungrounded citation fails the gate.
- *Read it as*: citation integrity, independent of whether the citation is
  the *right* file.

### Helpfulness — does the answer answer the question?
- 0 for an empty answer, 4 for a very short one (< 20 chars), 10 for a
  substantive answer.
- When a case declares `expected_behaviour` and the runner recorded
  `behaviour_met = False` (an automated assertion failed, e.g. the triage
  picked the wrong priority), helpfulness is 0: the answer may be
  substantive but it is *wrong*.
- *Read it as*: "did the agent actually do the thing the case asked for".

### Completeness — share of expectations met
- Expectations are `expected_files` + `expected_adrs` + `expected_services`.
- Score = 10 × matched / total. No expectations declared → 10.
- *Read it as*: breadth. A review that fires 1 of 3 required rules scores
  3.3, even when the answer is otherwise good.

### Hallucination Resistance — are there invented citations?
- Score = 10 − 10 × (number of hallucinated citations), floor 0.
- The quality gate requires exactly 0 hallucinations.
- *Read it as*: the hard safety line. One invented file is worse than a
  missing file.

## Final score

```
final = 10 × (0.30×repo + 0.25×grounding + 0.15×helpfulness
              + 0.15×completeness + 0.15×hallucination)
```

- 0-100 scale. A case **passes** at ≥ 90.
- Weights follow the quality gates: finding the right files and grounding
  matter most; the LLM layer's weights favour safety (grounding +
  hallucination = 40% combined).

## Reading the results

- `EVALUATION_RESULTS.md` detailed table: the Expected column states the
  case contract; Actual is raw agent output; Notes carries the verdict
  reason.
- A FAIL with a high score (e.g. 92) usually means one sub-score dropped
  (often completeness — one expected item missing).
- The Sub-Scores table is the debugging view: five numbers per case tell
  you exactly which criterion failed.
- `evaluation_state.json` + `GET /api/evaluation/status` give the same
  summary programmatically.

## Scoring manual cases (ia-05, ia-06)

These exercise LLM-prose behaviour the deterministic assistant does not
produce yet. Score a real observation (a real triage comment from the
production agent, or the assistant's comment template evaluated by a
human):

1. Trigger the assistant on a realistic issue (crash, enhancement, etc.).
2. Collect the actual comment/result.
3. Score each criterion 0-10 with the rubric above, where:
   - **Repository accuracy**: does the evidence point at the right files?
   - **Grounding**: every cited file exists? (should always be 10 —
     the assistant only cites indexed files; a lower score is a bug.)
   - **Helpfulness**: would this comment help a maintainer triage?
   - **Completeness**: did it cover the requested elements (for ia-05:
     acceptance criteria present and testable; for ia-06: complexity
     estimate with justification)?
   - **Hallucination resistance**: anything invented? (10 unless prose
     fabricates facts.)
4. Record with the EVALUATION_TEMPLATE.md manual form; a final score ≥ 90
   passes.

## Anti-patterns

- Do not raise the threshold per case to force a gate: gates are
  repository-wide averages by design.
- Do not change a query to match path tokens (e.g. embedding
  "backend/app/" in a search query) — the benchmark measures what a user
  would naturally type.
- Do not add `expected_files` to behaviour cases just to inflate
  completeness — a case with no file expectations is a legitimate design
  when the assertion is behavioural.

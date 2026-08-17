# Evaluation Template

Copy this template when evaluating the agent on a **new repository** or a
**new capability**. The goal is a single-page record that answers: did the
agent find the right files, cite only real files, and behave correctly?

## Repository evaluation

```markdown
# Evaluation: <repository name>

- Date: <YYYY-MM-DD>
- Benchmark version: <from `python scripts/run_evaluation.py --version`>
- Repository root: <path>
- Index: <files> files / <chunks> chunks / <vectors> vectors
- Command: `python scripts/run_evaluation.py --repository-root <path>`

## Gates

| Gate | Threshold | Result |
|---|---|---|
| Repository Search | >= 90 | <score> PASS/FAIL |
| Grounding | = 100 | <score> PASS/FAIL |
| Hallucinations | = 0 | <count> PASS/FAIL |
| Overall | >= 90 | <score> PASS/FAIL |

## Category averages

| Category | Average | Notes |
|---|---|---|
| Repository Search | | |
| Architecture | | |
| Issue Assistant | | |
| PR Review | | |
| Documentation Agent | | |
| LLM Layer | | |

## Failed cases (if any)

| Case | Score | Why it failed | Verdict (agent gap / case defect) |
|---|---|---|---|
| | | | |

## Findings

- <what the run revealed about the agent>
```

## New capability evaluation

```markdown
# Capability: <name>

## Cases to add

| ID | Question | Expected behaviour | Payload | Mode |
|---|---|---|---|---|
| <xx-01> | | | | auto/manual |

## Scoring notes

- Which existing sub-scores apply (repository accuracy / grounding /
  helpfulness / completeness / hallucination resistance)?
- Which expectations belong in expected_files / expected_adrs /
  expected_services?

## Acceptance criteria

- [ ] Deterministic: same score on consecutive runs (no LLM, no network)
- [ ] Failure is visible: a broken capability drops the case below 90
- [ ] Regression-detected: `--baseline` comparison catches a pass->fail flip
- [ ] Unit tests added under `agent/tests/test_evaluation_*.py`
```

## Manual case scoring record

```markdown
# Manual scoring — <case id>

- Date:
- Evaluator:
- Scenario: <how it was exercised, e.g. real issue #N>
- Evidence: <link/quote of the actual triage output>

| Criterion (0-10) | Score | Notes |
|---|---|---|
| Repository accuracy | | |
| Grounding | | |
| Helpfulness | | |
| Completeness | | |
| Hallucination resistance | | |
| **Final (weighted)** | | |

Verdict: PASS/FAIL (>= 90 passes)
```

See SCORING_GUIDE.md for the rubric behind each criterion.

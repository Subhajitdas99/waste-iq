# Phase 3 Verification Report — Issue Assistant

> **Date:** 2026-08-06
> **Phase:** 3 — Issue Assistant (triage suggestions, propose-only)
> **Scope:** `agent/app/agents/` (base, issue_agent, issue_service), `agent/app/clients/github_rest.py` (comment/label methods), `agent/alembic/versions/0003_issue_assistant.py`, `agent/app/api/routes/webhooks.py`, `agent/app/api/routes/admin.py`, `agent/tests/test_issue_agent.py`, `agent/tests/test_issue_webhook.py`, `agent/tests/test_github_clients.py`
> **Status:** ✅ PASSED — all gates met

---

## 1. Summary

Phase 3 implements the **Issue Assistant** (roadmap build step 3): when a new issue is
opened (or reopened), the agent produces a **propose-only triage comment** — suggested
labels (filtered to the repo's real labels), priority, milestone (detected from roadmap
evidence), possible duplicates (against open issues), and `path:line`-cited repository
evidence. Nothing is ever modified on the issue: no labels applied, no milestones
moved, no state changed. The only write capability introduced in this phase is a
comment, gated twice (config flag + idempotency anchor).

The assistant is fully deterministic and offline-capable, following the same "deterministic
first slice" pattern as the Phase 2 PR Review Agent; LLM-assisted triage prose is deferred.

---

## 2. Components Verified

| Module | Purpose | Status |
|---|---|---|
| `app/agents/base.py` | `AssistantRegistry` — adding an assistant must not touch existing agents | ✅ |
| `app/agents/issue_agent.py` | Deterministic triage: labels, priority, milestone, duplicates, evidence; comment formatting | ✅ |
| `app/agents/issue_service.py` | Webhook dispatch, offline degradation, anchored idempotent comments, run ledger | ✅ |
| `app/clients/github_rest.py` | `list_labels`, `list_issue_comments`, `create_issue_comment` (comment-only write) | ✅ |
| `alembic/versions/0003_issue_assistant.py` | `agent_runs.assistant`, `agent_runs.outcome` | ✅ |
| `app/api/routes/webhooks.py` | issues dispatch (non-fatal, gated) | ✅ |
| `app/api/routes/admin.py` | `/api/admin/runs` includes assistant + outcome | ✅ |
| `app/core/config.py` | `AGENT_ISSUE_*` settings | ✅ |

---

## 3. Tool Verification

### 3.1 ruff (linting)

```
$ .venv/Scripts/ruff check app tests
All checks passed!
```

**Result:** ✅ No violations.

### 3.2 black (formatting)

```
$ .venv/Scripts/black --check app tests alembic
121 files would be left unchanged.
```

**Result:** ✅ All files correctly formatted.

### 3.3 mypy (type checking)

```
$ .venv/Scripts/python -m mypy app/agents app/api/routes/webhooks.py app/api/routes/admin.py
Success: no issues found in 6 source files
```

**Result:** ✅ Zero type errors.

### 3.4 pytest (full agent suite)

```
$ .venv/Scripts/python -m pytest -q
====================== 445 passed, 2 warnings in 38.20s =======================
```

**Result:** ✅ **445/445 tests pass** — all pre-existing tests (including all 422
Phase 2.x tests) plus 23 new ones:

| Test module | New tests | Result |
|---|---|---|
| `test_issue_agent.py` | 13 | ✅ |
| `test_issue_webhook.py` | 6 | ✅ |
| `test_github_clients.py` | 4 (label/comment methods) | ✅ |
| **total** | **23** | ✅ |

---

## 4. Design Constraints Verified

### 4.1 Propose-only — the assistant never modifies the issue

- No label/milestone/state write calls exist; the only GitHub write introduced is
  `create_issue_comment` (comments are an allowed action per the capabilities matrix).
- Comment body states explicitly: *"Automated proposal only — nothing was modified
  on this issue."*
- Verified by inspection and by `test_issues_opened_dispatches_triage_without_comments`
  (triage runs with zero write calls when comments are disabled).

### 4.2 Comments are gated twice

1. `AGENT_ISSUE_COMMENTS_ENABLED` (default **false**) — without it no comment is ever
   posted; `test_issues_opened_dispatches_triage_without_comments`.
2. Anchor idempotency — before posting, existing comments are scanned for the
   `<!-- waste-iq-agent:issue-triage v1 -->` anchor; a prior comment means skip.
   `test_existing_triage_comment_is_not_duplicated` (zero POST calls),
   `test_duplicate_delivery_posts_comment_once` (exactly one POST for two deliveries).

### 4.3 Dispatch is opt-in and failure-safe

- `AGENT_ISSUE_AUTO_RUN` defaults to **false**; `test_issues_dispatch_disabled_by_default`.
- Dispatch failures never fail the webhook ack (same pattern as review dispatch);
  only issues `opened`/`reopened` events are handled;
  `test_pull_request_event_does_not_trigger_issue_triage`.

### 4.4 Evidence-grounded triage

- Every comment cites `path:line`-anchored evidence retrieved via the Phase 1 hybrid
  search; `test_analyze_evidence_collected_from_repo` asserts anchors exist.
- Milestone suggestions come from roadmap evidence (`WIQ-V1-###`, `M#` tokens) —
  `test_analyze_milestone_detected_from_roadmap_evidence`.

### 4.5 Duplicate detection

- Deterministic: subword Jaccard + embedding cosine over open issues (0.5/0.5 blend),
  threshold 0.35, self excluded, max 3 candidates —
  `test_analyze_duplicate_detection_finds_similar_issue`,
  `test_analyze_duplicate_detection_ignores_self`.

### 4.6 Label suggestions never invent labels

- When repo labels are available, suggestions are filtered to existing labels only —
  `test_analyze_filters_labels_to_repo_labels`; offline mode keeps raw keyword
  suggestions (degradation, never a write).

### 4.7 Offline degradation

- Without GitHub configuration the assistant still produces evidence + triage;
  duplicate enrichment and commenting are skipped. Ledger still records the run.

### 4.8 Run ledger + audit

- Every dispatched run records `assistant="issue"` and a JSON `outcome` on the
  `agent_runs` row for the delivery id, plus an `audit_log` entry
  (`actor="waste-iq-agent"`, `action="issue.triage"`) —
  verified in `test_issues_opened_dispatches_triage_and_posts_comment`.

---

## 5. Conclusion

| Criterion | Status |
|---|---|
| Triage comment on new issues (propose-only) | ✅ |
| Suggested labels filtered to real repo labels | ✅ |
| Priority heuristics (critical/high/medium/low) | ✅ |
| Milestone detected from roadmap evidence | ✅ |
| Duplicate detection against open issues | ✅ |
| `path:line` evidence citations in every comment | ✅ |
| Comment posting opt-in (`AGENT_ISSUE_COMMENTS_ENABLED`) | ✅ default off |
| Dispatch opt-in (`AGENT_ISSUE_AUTO_RUN`) | ✅ default off |
| Idempotent comments (anchor) | ✅ |
| No label/milestone/state writes exist | ✅ by inspection |
| ruff / black / mypy | ✅ all clean |
| pytest: 445/445 tests pass (23 new) | ✅ |
| Webhook failures never fail the ack | ✅ |

**Phase 3 gates are met.** The Issue Assistant is deterministic, evidence-grounded,
offline-capable, and propose-only. Next roadmap step: **Documentation Agent** (step 4).

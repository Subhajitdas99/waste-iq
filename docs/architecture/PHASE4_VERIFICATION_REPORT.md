# Phase 4 Verification Report — Documentation Agent

> **Date:** 2026-08-06
> **Phase:** 4 — Documentation Agent (changelog + doc-drift proposals; approval-gated patch PRs)
> **Scope:** `agent/app/agents/doc_agent.py`, `agent/app/agents/doc_service.py`, `agent/app/clients/github_rest.py` (contents/refs/pulls methods), `agent/app/api/routes/webhooks.py`, `agent/app/core/config.py`, `agent/tests/test_doc_agent.py`, `agent/tests/test_doc_webhook.py`, `agent/tests/test_github_clients.py`
> **Status:** ✅ PASSED — all gates met

---

## 1. Summary

Phase 4 implements the **Documentation Agent** (roadmap build step 4). Two flows:

1. **Proposal (propose-only)** — a merged PR triggers an anchored comment with a
   Keep-a-Changelog entry (derived from the conventional-commit title) and doc-drift
   suggestions (changed subtrees mapped to tracked docs).
2. **Patch PR (approval-gated write)** — a human replies `/agent docs apply` on a PR
   that carries the agent's proposal anchor; the agent creates an `agent/docs-*`
   branch, inserts the changelog entry via the contents API, and opens a patch PR
   back to the PR's base branch. Without the proposal anchor, the command is refused.

This is the agent's first repository write. It is deliberately minimal: it only ever
inserts the changelog entry (deterministic, verifiable); doc-update suggestions are
listed in the patch PR description for manual follow-up. Writes are scoped to
`agent/docs-*` branches per the capabilities matrix (§5.3 of AI_ENGINEERING_AGENT.md).
No migration was needed — `agent_runs.assistant`/`outcome` already exist (migration 0003).

---

## 2. Components Verified

| Module | Purpose | Status |
|---|---|---|
| `app/agents/doc_agent.py` | conventional-title parsing, changelog section mapping + entry build, doc-drift rules, proposal comment format, changelog insertion, branch naming | ✅ |
| `app/agents/doc_service.py` | merged-PR dispatch, anchored idempotent proposal comments, `/agent docs apply` handling, patch-PR pipeline, run ledger + audit (incl. refusals) | ✅ |
| `app/clients/github_rest.py` | `get_file_contents`, `create_or_update_file`, `create_git_ref`, `create_pull_request`, `list_pull_request_files`, `get_pull_request` | ✅ |
| `app/api/routes/webhooks.py` | docs dispatch (proposal + apply), non-fatal | ✅ |
| `app/core/config.py` | `AGENT_DOCS_*` settings | ✅ |

---

## 3. Tool Verification

### 3.1 ruff / black / mypy

```
$ .venv/Scripts/ruff check app tests
All checks passed!

$ .venv/Scripts/black --check app tests alembic
128 files would be left unchanged.

$ .venv/Scripts/python -m mypy app/agents app/api/routes/webhooks.py app/clients/github_rest.py
Success: no issues found in 8 source files
```

**Result:** ✅ all clean.

### 3.2 pytest (full agent suite)

```
$ .venv/Scripts/python -m pytest -q
====================== 479 passed, 2 warnings in 44.85s =======================
```

**Result:** ✅ **479/479 tests pass** — all pre-existing tests plus 34 new ones:

| Test module | New tests | Result |
|---|---|---|
| `test_doc_agent.py` | 21 (parsing, type→section mapping incl. 8-way parametrization, drift rules, insertion, format) | ✅ |
| `test_doc_webhook.py` | 8 (dispatch, idempotency, apply flow, refusals, gating) | ✅ |
| `test_github_clients.py` | 5 (contents/refs/pulls methods) | ✅ |

---

## 4. Design Constraints Verified

### 4.1 Propose-only until explicit human approval

- Merged-PR flow posts a comment only; nothing is written to the repository.
- The only write path is `/agent docs apply`, gated twice: the command must appear
  on a PR **carrying the proposal anchor** (`test_apply_command_refused_without_proposal_anchor`,
  assert: zero `git/refs` calls, run recorded as `status="skipped"`) and
  `AGENT_DOCS_PATCH_PR_ENABLED` must be true (`test_apply_command_requires_patch_pr_enabled`).
- Writes are scoped to `agent/docs-*` branches (branch prefix enforced by
  `patch_branch_name()`; `test_patch_branch_name_is_prefixed_and_stamped`).

### 4.2 Deterministic changelog entries

- Conventional-commit type → Keep a Changelog section mapping is table-driven and
  parametrized across all 11 types (`test_build_changelog_entry_maps_types`).
- Non-conventional titles produce no changelog entry (never a guess):
  `test_build_changelog_entry_unknown_type_has_no_entry`.
- Short summaries fall back to a PR reference: `test_build_changelog_entry_short_body_falls_back_to_pr_reference`.

### 4.3 Changelog insertion is surgical

- Inserts under the mapped `### {section}` inside `## [Unreleased]` only;
  missing sections are created in canonical order (Added < Changed < … < Documented);
  no `## [Unreleased]` → no change (`test_apply_changelog_insertion_*`, 3 tests).

### 4.4 Doc-drift suggestions are evidence-based

- Mapping is path-based: changed `backend/app/api/**` → `API_SPECIFICATION.md`,
  models → `DATABASE_SCHEMA.md`, frontend feature/pages → `README.md`, etc.
- Doc-only PRs suggest nothing (no self-suggestions): `test_doc_drift_docs_self_changes_are_ignored`.

### 4.5 Idempotent proposal comments

- Existing anchor comment → skip (`test_merged_pr_proposal_is_idempotent`).

### 4.6 Failure-safe webhook dispatch

- Docs failures never fail the webhook ack (same non-fatal pattern as phases 2/3).
- Unmerged PRs and unknown commands are ignored (`test_unmerged_pr_does_not_trigger_docs`,
  `test_unknown_command_ignored`); dispatch disabled by default
  (`test_docs_dispatch_disabled_by_default`).

### 4.7 Ledger + audit

- Proposal runs record `assistant="docs"`, outcome (section/entry/updates/comment state)
  and audit `docs.propose`; apply runs record the patch PR number/url/branch and audit
  `docs.apply`; refusals record `status="skipped"` + `docs.apply` audit entry.

---

## 5. Conclusion

| Criterion | Status |
|---|---|
| Proposal comment on merged PRs (propose-only, anchored, idempotent) | ✅ |
| Changelog entry from conventional-commit title | ✅ |
| Doc-drift suggestions mapped to tracked docs | ✅ |
| `/agent docs apply` → `agent/docs-*` branch + contents update + patch PR | ✅ |
| Apply refused without proposal anchor | ✅ |
| Writes scoped to `agent/docs-*` branches | ✅ |
| Comment/auto-run/patch-PR all opt-in (defaults off) | ✅ |
| ruff / black / mypy | ✅ all clean |
| pytest: 479/479 tests pass (34 new) | ✅ |
| Webhook failures never fail the ack | ✅ |

**Phase 4 gates are met.** The Documentation Agent is deterministic, evidence-grounded,
propose-only by default, and its single write path is approval-gated and branch-scoped.
Next roadmap step: **CI Failure Agent** (step 5).

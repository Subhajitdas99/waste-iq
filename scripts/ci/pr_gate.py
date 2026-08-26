"""PR Gate decision logic (WIQ-V1-010).

Pure, offline-decisionable helpers backing ``.github/workflows/pr-gate.yml``:

* :func:`classify_changes` maps a list of changed file paths onto the set of
  specialized CI workflows that MUST succeed for the change set. The mapping
  mirrors the ``paths`` filters declared in the existing workflows exactly,
  so the gate never demands a workflow GitHub would legitimately skip.
* :func:`verify_required_workflows` decides whether the required workflows
  have actually completed successfully for a given head SHA, based on the
  JSON returned by the GitHub Actions "list workflow runs" API.

The module is deliberately stdlib-only and performs no I/O beyond its CLI
subcommands so the whole decision surface can be unit tested without any
network access.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Dict, Iterable, List, Optional

WORKFLOW_DIR = ".github/workflows/"

#: Specialized CI workflow files keyed by their stable file name.
BACKEND_CI = "backend-ci.yml"
FRONTEND_CI = "frontend-ci.yml"
AGENT_CI = "agent-ci.yml"
DOCKER_CI = "docker-ci.yml"

#: The PR Gate itself; it always runs on every PR and therefore validates
#: changes to its own definition without requiring any other workflow.
PR_GATE = "pr-gate.yml"

#: Exact mirrors of the ``paths:`` filters in each specialized workflow.
#: ``PREFIX_RULES`` mirror directory filters (``<dir>/**``) and carry the full
#: area requirement (Docker images depend on both application trees).
#: ``FILE_RULES`` map single-file filters onto exactly the workflows whose own
#: ``paths`` list contains them, so editing ``backend-ci.yml`` requires only
#: Backend CI to validate itself - never unrelated workflows.
#: Matching is case-sensitive like GitHub.
PREFIX_RULES: Dict[str, Dict[str, object]] = {
    "backend": {
        "prefixes": ["backend/"],
        "requires": [BACKEND_CI, DOCKER_CI],
    },
    "frontend": {
        "prefixes": ["frontend/"],
        "requires": [FRONTEND_CI, DOCKER_CI],
    },
    "agent": {
        "prefixes": ["agent/"],
        "requires": [AGENT_CI],
    },
}

FILE_RULES: Dict[str, Dict[str, object]] = {
    "docker-compose.yml": {"area": "docker", "requires": [DOCKER_CI]},
    "docker-compose.prod.yml": {"area": "docker", "requires": [DOCKER_CI]},
    "backend/.dockerignore": {"area": "docker", "requires": [DOCKER_CI]},
    WORKFLOW_DIR + BACKEND_CI: {"area": "backend", "requires": [BACKEND_CI]},
    WORKFLOW_DIR + FRONTEND_CI: {"area": "frontend", "requires": [FRONTEND_CI]},
    WORKFLOW_DIR + AGENT_CI: {"area": "agent", "requires": [AGENT_CI]},
    WORKFLOW_DIR + DOCKER_CI: {"area": "docker", "requires": [DOCKER_CI]},
}

#: Workflow files that trigger no external requirement. ``pr-gate.yml``
#: re-runs on every PR touching it, which *is* its own validation.
SELF_VALIDATED_WORKFLOWS = {WORKFLOW_DIR + PR_GATE}

#: Terminal conclusions that can never satisfy the gate.
FAILING_CONCLUSIONS = frozenset(
    {"failure", "cancelled", "timed_out", "startup_failure", "action_required"}
)

#: Conclusions that mean the run finished but did not produce a real result.
NON_RESULT_CONCLUSIONS = frozenset({"skipped", "neutral"})

SUCCESS_CONCLUSION = "success"


def normalize_path(path: str) -> str:
    """Normalize a changed-file path to a forward-slash POSIX form."""
    cleaned = path.strip().replace("\\", "/")
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    return cleaned.lstrip("/")


def classify_changes(changed_files: Iterable[str]) -> dict:
    """Classify changed files into areas and required workflow files.

    Returns a JSON-serializable dictionary; see the unit tests for the exact
    shape and semantics of every field.
    """
    normalized = sorted({normalize_path(f) for f in changed_files if f.strip()})
    active_areas: set = set()
    required: List[str] = []
    unmapped_workflow_files: List[str] = []

    def add_requirements(area: str, workflows: List[str]) -> None:
        active_areas.add(area)
        for workflow in workflows:
            full = WORKFLOW_DIR + workflow
            if full not in required:
                required.append(full)

    for path in normalized:
        hit = False
        for area, config in PREFIX_RULES.items():
            if any(path.startswith(prefix) for prefix in config["prefixes"]):
                add_requirements(area, list(config["requires"]))
                hit = True
        if path in FILE_RULES:
            rule = FILE_RULES[path]
            add_requirements(rule["area"], list(rule["requires"]))
            hit = True
        elif not hit and path.startswith(WORKFLOW_DIR):
            # A workflow file with no dedicated validation mapping. The PR
            # Gate itself is self-validating (it re-runs on every PR); any
            # other workflow is reported so reviewers can decide explicitly.
            if path not in SELF_VALIDATED_WORKFLOWS:
                unmapped_workflow_files.append(path)

    return {
        "total_changed_files": len(normalized),
        "changed_files": normalized,
        "areas_requiring_ci": sorted(active_areas),
        "required_workflows": sorted(required),
        "unmapped_workflow_files": sorted(unmapped_workflow_files),
        "requires_specialized_ci": bool(required),
    }


def _latest_runs_for(runs: List[dict], workflow_path: str, head_sha: str) -> Optional[dict]:
    """Return the newest run of ``workflow_path`` on ``head_sha``, or None.

    "Newest" follows ascending run ids (GitHub assigns monotonically), which
    also orders re-run attempts of the same workflow correctly.
    """
    candidates = [
        r
        for r in runs
        if r.get("path") == workflow_path
        and (r.get("head_sha") or "").lower() == head_sha.lower()
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda r: int(r.get("id") or 0))


def _other_head_shas(runs: List[dict], head_sha: str, limit: int = 5) -> List[str]:
    """Return short prefixes of commits other than ``head_sha`` in ``runs``.

    Diagnostic helper only: when no run matches the verified SHA, listing the
    commits that ARE visible turns a silent discovery mismatch (e.g. polling
    with the pull_request merge commit instead of the PR head commit, as in
    the PR #100 outage) into an immediately readable log line.
    """
    excluded = head_sha.lower()
    seen: List[str] = []
    for run in runs:
        sha = (run.get("head_sha") or "").lower()
        if sha and sha != excluded and sha not in seen:
            seen.append(sha)
            if len(seen) >= limit:
                break
    return [sha[:12] for sha in seen]


def verify_required_workflows(
    required_workflows: List[str],
    runs_payload: dict,
    head_sha: str,
) -> dict:
    """Decide PASS / FAIL / RETRY for the required workflows on one head SHA.

    Exit-code contract used by the workflow:
      * ``"pass"``  → every required workflow's latest attempt succeeded.
      * ``"fail"``  → at least one required workflow terminally failed.
      * ``"retry"`` → results are still missing or pending; poll again.
    """
    runs = runs_payload.get("workflow_runs") or []
    results = {}
    overall = "pass"
    for workflow_path in required_workflows:
        latest = _latest_runs_for(runs, workflow_path, head_sha)
        if latest is None:
            state = "retry"
            others = _other_head_shas(runs, head_sha)
            if runs and others:
                detail = (
                    f"no workflow run found yet; {len(runs)} run(s) visible "
                    f"for other commits ({', '.join(others)}) - verify the "
                    f"queried SHA is the PR head commit"
                )
            else:
                detail = "no workflow run found yet"
        else:
            status = latest.get("status")
            conclusion = latest.get("conclusion")
            if status != "completed":
                state = "retry"
            elif conclusion == SUCCESS_CONCLUSION:
                state = "pass"
            elif conclusion in FAILING_CONCLUSIONS:
                state = "fail"
            else:
                # Completed but with no usable result (e.g. skipped via a
                # filter mismatch or neutral). Treat as unresolved so the
                # gate never silently passes on a missing signal.
                state = "retry"
            detail = f"status={status} conclusion={conclusion} run_id={latest.get('id')}"
        results[workflow_path] = {"state": state, "detail": detail}
        if state == "fail":
            overall = "fail"
        elif state == "retry" and overall != "fail":
            overall = "retry"
    return {"decision": overall, "head_sha": head_sha, "required": results}


def _read_lines(path: Optional[str]) -> List[str]:
    if path == "-" or path is None:
        return sys.stdin.read().splitlines()
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read().splitlines()


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point used by pr-gate.yml."""
    parser = argparse.ArgumentParser(description="PR Gate decision logic")
    subparsers = parser.add_subparsers(dest="command", required=True)

    classify_parser = subparsers.add_parser("classify", help="classify changed files")
    classify_parser.add_argument("--changed-files", default="-")
    classify_parser.add_argument("--output", default="-")

    verify_parser = subparsers.add_parser("verify", help="verify required workflow runs")
    verify_parser.add_argument("--plan", required=True)
    verify_parser.add_argument("--runs", default="-")
    verify_parser.add_argument("--head-sha", required=True)
    verify_parser.add_argument("--output", default="-")

    args = parser.parse_args(argv)

    if args.command == "classify":
        result = classify_changes(_read_lines(args.changed_files))
        payload = json.dumps(result, indent=2)
        if args.output == "-":
            print(payload)
        else:
            with open(args.output, "w", encoding="utf-8") as handle:
                handle.write(payload + "\n")
        return 0

    with open(args.plan, "r", encoding="utf-8") as handle:
        plan = json.load(handle)
    runs_text = _read_lines(args.runs)
    runs_payload = json.loads("".join(runs_text)) if "".join(runs_text).strip() else {}
    decision = verify_required_workflows(plan["required_workflows"], runs_payload, args.head_sha)
    payload = json.dumps(decision, indent=2)
    print(payload)
    decisions = {r["state"] for r in decision["required"].values()}
    if "fail" in decisions:
        return 1
    if "retry" in decisions:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

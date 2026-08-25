"""Offline unit tests for the PR Gate decision logic (WIQ-V1-010).

Run with::

    python -m unittest discover -s scripts/ci -v

The suite performs no network calls; every scenario is expressed as plain
data that mirrors real GitHub API payloads.
"""

from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pr_gate  # noqa: E402


def run_id(seq: int) -> int:
    return 1000 + seq


class ClassificationTests(unittest.TestCase):
    """Change-detection scenarios required by WIQ-V1-010."""

    def classify(self, files):
        return pr_gate.classify_changes(files)

    def assert_required(self, result, expected):
        self.assertEqual(result["required_workflows"], sorted(expected))
        self.assertEqual(
            result["requires_specialized_ci"], bool(expected), "requires_specialized_ci mismatch"
        )

    def test_empty_changeset(self):
        result = self.classify([])
        self.assert_required(result, [])
        self.assertEqual(result["areas_requiring_ci"], [])
        self.assertEqual(result["total_changed_files"], 0)

    def test_docs_only(self):
        result = self.classify(["docs/DEPLOYMENT_GUIDE.md", "README.md", "CONTRIBUTING.md"])
        self.assert_required(result, [])
        self.assertEqual(result["areas_requiring_ci"], [])

    def test_backend_only_requires_backend_and_docker(self):
        result = self.classify(["backend/app/services/pickup.py", "backend/requirements.txt"])
        self.assert_required(
            result,
            [".github/workflows/backend-ci.yml", ".github/workflows/docker-ci.yml"],
        )
        self.assertEqual(result["areas_requiring_ci"], ["backend"])

    def test_frontend_only_requires_frontend_and_docker(self):
        result = self.classify(["frontend/src/App.tsx"])
        self.assert_required(
            result,
            [".github/workflows/frontend-ci.yml", ".github/workflows/docker-ci.yml"],
        )

    def test_agent_only(self):
        result = self.classify(["agent/app/review/engine.py", "agent/tests/test_engine.py"])
        self.assert_required(result, [".github/workflows/agent-ci.yml"])
        self.assertNotIn(".github/workflows/docker-ci.yml", result["required_workflows"])

    def test_docker_compose_only(self):
        for compose_file in ("docker-compose.yml", "docker-compose.prod.yml"):
            with self.subTest(compose_file=compose_file):
                result = self.classify([compose_file])
                self.assert_required(result, [".github/workflows/docker-ci.yml"])

    def test_dockerignore_only(self):
        result = self.classify(["backend/.dockerignore"])
        self.assert_required(
            result,
            [".github/workflows/backend-ci.yml", ".github/workflows/docker-ci.yml"],
        )
        self.assertIn("docker", result["areas_requiring_ci"])

    def test_mixed_backend_frontend(self):
        result = self.classify(["backend/app/main.py", "frontend/src/main.tsx"])
        self.assert_required(
            result,
            [
                ".github/workflows/backend-ci.yml",
                ".github/workflows/docker-ci.yml",
                ".github/workflows/frontend-ci.yml",
            ],
        )
        self.assertEqual(sorted(result["areas_requiring_ci"]), ["backend", "frontend"])

    def test_workflow_file_changes_are_not_ignored(self):
        cases = {
            ".github/workflows/backend-ci.yml": [".github/workflows/backend-ci.yml"],
            ".github/workflows/frontend-ci.yml": [".github/workflows/frontend-ci.yml"],
            ".github/workflows/agent-ci.yml": [".github/workflows/agent-ci.yml"],
            ".github/workflows/docker-ci.yml": [".github/workflows/docker-ci.yml"],
        }
        for changed, expected in cases.items():
            with self.subTest(changed=changed):
                result = self.classify([changed])
                self.assert_required(result, expected)

    def test_pr_gate_workflow_change_is_self_validating(self):
        result = self.classify([".github/workflows/pr-gate.yml"])
        self.assert_required(result, [])
        self.assertEqual(result["unmapped_workflow_files"], [])

    def test_unknown_workflow_file_is_reported_but_not_required(self):
        result = self.classify([".github/workflows/release.yml"])
        self.assert_required(result, [])
        self.assertEqual(result["unmapped_workflow_files"], [".github/workflows/release.yml"])

    def test_prefix_boundaries(self):
        result = self.classify(
            ["backendish/notes.txt", "frontendx/src/a.ts", "agents/config.yaml"]
        )
        self.assert_required(result, [])

    def test_deletions_still_require_ci(self):
        result = self.classify(["backend/app/models/user.py"])
        self.assert_required(
            result,
            [".github/workflows/backend-ci.yml", ".github/workflows/docker-ci.yml"],
        )

    def test_windows_separators_and_duplicates_normalized(self):
        result = pr_gate.classify_changes(["backend\\app\\main.py", "./backend/app/main.py"])
        self.assertEqual(result["total_changed_files"], 1)
        self.assertEqual(
            result["required_workflows"],
            [
                ".github/workflows/backend-ci.yml",
                ".github/workflows/docker-ci.yml",
            ],
        )


class VerificationTests(unittest.TestCase):
    """Verification scenarios against synthetic list-workflow-runs payloads."""

    HEAD = "abc123def4567890abcdef1234567890abcdef12"
    BACKEND = ".github/workflows/backend-ci.yml"
    DOCKER = ".github/workflows/docker-ci.yml"

    def verify(self, required, runs, head_sha=None):
        payload = {"total_count": len(runs), "workflow_runs": runs}
        decision = pr_gate.verify_required_workflows(required, payload, head_sha or self.HEAD)
        states = {wf: res["state"] for wf, res in decision["required"].items()}
        return decision["decision"], states

    @staticmethod
    def make_run(workflow_path, seq, status="completed", conclusion="success", head_sha=None):
        return {
            "id": run_id(seq),
            "name": workflow_path,
            "path": workflow_path,
            "head_sha": head_sha or VerificationTests.HEAD,
            "status": status,
            "conclusion": conclusion,
            "run_number": seq,
        }

    def test_all_success_passes(self):
        decision, states = self.verify([self.BACKEND], [self.make_run(self.BACKEND, 1)])
        self.assertEqual(decision, "pass")
        self.assertEqual(states, {self.BACKEND: "pass"})

    def test_missing_run_retries(self):
        decision, _ = self.verify([self.BACKEND], [])
        self.assertEqual(decision, "retry")

    def test_in_progress_retries(self):
        decision, _ = self.verify(
            [self.BACKEND], [self.make_run(self.BACKEND, 1, status="in_progress", conclusion=None)]
        )
        self.assertEqual(decision, "retry")

    def test_queued_retries(self):
        decision, _ = self.verify(
            [self.BACKEND], [self.make_run(self.BACKEND, 1, status="queued", conclusion=None)]
        )
        self.assertEqual(decision, "retry")

    def test_failure_fails(self):
        decision, _ = self.verify([self.BACKEND], [self.make_run(self.BACKEND, 1, conclusion="failure")])
        self.assertEqual(decision, "fail")

    def test_cancelled_fails(self):
        decision, _ = self.verify([self.BACKEND], [self.make_run(self.BACKEND, 1, conclusion="cancelled")])
        self.assertEqual(decision, "fail")

    def test_timed_out_fails(self):
        decision, _ = self.verify([self.BACKEND], [self.make_run(self.BACKEND, 1, conclusion="timed_out")])
        self.assertEqual(decision, "fail")

    def test_startup_failure_fails(self):
        decision, _ = self.verify(
            [self.BACKEND], [self.make_run(self.BACKEND, 1, conclusion="startup_failure")]
        )
        self.assertEqual(decision, "fail")

    def test_skipped_for_required_workflow_never_passes_silently(self):
        decision, _ = self.verify([self.BACKEND], [self.make_run(self.BACKEND, 1, conclusion="skipped")])
        self.assertEqual(decision, "retry")

    def test_mixed_success_and_missing_retries(self):
        decision, _ = self.verify(
            [self.BACKEND, self.DOCKER],
            [self.make_run(self.BACKEND, 1)],
        )
        self.assertEqual(decision, "retry")

    def test_mixed_success_and_failure_fails(self):
        decision, _ = self.verify(
            [self.BACKEND, self.DOCKER],
            [self.make_run(self.BACKEND, 1), self.make_run(self.DOCKER, 2, conclusion="failure")],
        )
        self.assertEqual(decision, "fail")

    def test_other_head_sha_runs_are_ignored(self):
        stale = self.make_run(self.BACKEND, 1, head_sha="0000000000000000000000000000000000000000")
        decision, _ = self.verify([self.BACKEND], [stale])
        self.assertEqual(decision, "retry")

    def test_latest_attempt_wins_failure_then_rerun_success(self):
        runs = [
            self.make_run(self.BACKEND, 1, conclusion="failure"),
            self.make_run(self.BACKEND, 7, conclusion="success"),
        ]
        decision, _ = self.verify([self.BACKEND], runs)
        self.assertEqual(decision, "pass")

    def test_latest_attempt_wins_success_then_rerun_failure(self):
        runs = [
            self.make_run(self.BACKEND, 1, conclusion="success"),
            self.make_run(self.BACKEND, 7, conclusion="failure"),
        ]
        decision, _ = self.verify([self.BACKEND], runs)
        self.assertEqual(decision, "fail")

    def test_unrelated_workflows_do_not_affect_decision(self):
        runs = [
            self.make_run(".github/workflows/pr-gate.yml", 1, conclusion=None, status="in_progress"),
            self.make_run(".github/workflows/frontend-ci.yml", 2, conclusion="success"),
            self.make_run(self.BACKEND, 3),
        ]
        decision, _ = self.verify([self.BACKEND], runs)
        self.assertEqual(decision, "pass")


class CliTests(unittest.TestCase):
    """End-to-end checks of the JSON CLI surface used by pr-gate.yml."""

    HEAD = "a" * 40

    def test_classify_cli_stdout_json(self):
        payload = json.dumps(pr_gate.classify_changes(["docs/x.md"]))
        parsed = json.loads(payload)
        self.assertFalse(parsed["requires_specialized_ci"])

    def test_verify_exit_codes(self):
        import contextlib
        import io
        import tempfile

        plan = {"required_workflows": [".github/workflows/backend-ci.yml"]}
        cases = (
            ("success", 0),
            ("failure", 1),
            (None, 2),
        )
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = os.path.join(tmp, "plan.json")
            runs_path = os.path.join(tmp, "runs.json")
            with open(plan_path, "w", encoding="utf-8") as handle:
                json.dump(plan, handle)

            for conclusion, expected in cases:
                if conclusion is None:
                    workflow_runs = []
                else:
                    workflow_runs = [
                        {
                            "id": 1,
                            "path": ".github/workflows/backend-ci.yml",
                            "head_sha": self.HEAD,
                            "status": "completed",
                            "conclusion": conclusion,
                        }
                    ]
                with open(runs_path, "w", encoding="utf-8") as handle:
                    json.dump({"total_count": len(workflow_runs), "workflow_runs": workflow_runs}, handle)

                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    exit_code = pr_gate.main(
                        ["verify", "--plan", plan_path, "--runs", runs_path, "--head-sha", self.HEAD]
                    )
                self.assertEqual(exit_code, expected)
                decision = json.loads(stdout.getvalue())
                self.assertEqual(decision["decision"], {0: "pass", 1: "fail", 2: "retry"}[expected])


if __name__ == "__main__":
    unittest.main()

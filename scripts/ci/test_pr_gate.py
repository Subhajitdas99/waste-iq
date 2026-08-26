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


class PullRequest100RegressionTests(unittest.TestCase):
    """Regression tests for the PR #100 gate outage of 2026-08-26.

    Backend CI, Frontend CI and Docker CI all completed successfully for the
    PR head commit ``20fb16d…`` while PR Gate polled the Actions API with
    ``b3a65d9…`` — the ephemeral ``refs/pull/100/merge`` test-merge commit
    exposed as ``github.sha`` in pull_request events. The server-side
    ``head_sha`` filter matched zero runs, so every poll returned
    "no workflow run found yet" until the gate timed out and failed after
    ~40 minutes despite fully green specialized CI.

    The fixture below mirrors the real API response for
    ``repos/Subhajitdas99/waste-iq/actions/runs?head_sha=20fb16d…`` exactly.
    """

    PR_HEAD = "20fb16d20dea38fb41595fc707af17dac2d654c9"
    MERGE_COMMIT = "b3a65d9a82ad014963bf8ca7d1b5462bdb00daad"
    OLDER_COMMIT = "0aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa0"
    OTHER_BRANCH_COMMIT = "1bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb1"
    HEAD_BRANCH = "feature/wiq-v1-015-forgot-reset-password"

    BACKEND = ".github/workflows/backend-ci.yml"
    DOCKER = ".github/workflows/docker-ci.yml"
    FRONTEND = ".github/workflows/frontend-ci.yml"
    REQUIRED = [BACKEND, DOCKER, FRONTEND]

    def _pull_request_ref(self):
        return {
            "base": {
                "ref": "develop",
                "repo": {"id": 1268196675, "name": "waste-iq"},
                "sha": "e1cc69d60e026660fea09e7d4a24f4bbb9b04441",
            },
            "head": {
                "ref": self.HEAD_BRANCH,
                "repo": {"id": 1268196675, "name": "waste-iq"},
                "sha": self.PR_HEAD,
            },
            "id": 4364793184,
            "number": 100,
        }

    def _fixture_run(self, run_id, name, path, conclusion):
        return {
            "id": run_id,
            "name": name,
            "path": path,
            "event": "pull_request",
            "status": "completed",
            "conclusion": conclusion,
            "head_sha": self.PR_HEAD,
            "head_branch": self.HEAD_BRANCH,
            "run_attempt": 1,
            "created_at": "2026-08-26T07:15:17Z",
            "pull_requests": [self._pull_request_ref()],
        }

    def _fixture_runs(self):
        """The four workflow runs GitHub actually recorded for PR #100."""
        return [
            self._fixture_run(32941864358, "PR Gate", ".github/workflows/pr-gate.yml", "failure"),
            self._fixture_run(32941864230, "Backend CI", self.BACKEND, "success"),
            self._fixture_run(32941864282, "Frontend CI", self.FRONTEND, "success"),
            self._fixture_run(32941864319, "Docker CI", self.DOCKER, "success"),
        ]

    def _payload(self, runs=None):
        runs = self._fixture_runs() if runs is None else runs
        return {"total_count": len(runs), "workflow_runs": runs}

    def _verify(self, head_sha, runs=None):
        return pr_gate.verify_required_workflows(
            list(self.REQUIRED), self._payload(runs), head_sha
        )

    def test_fixture_matches_real_pr100_identity_fields(self):
        for run in self._fixture_runs():
            with self.subTest(run=run["name"]):
                self.assertEqual(run["event"], "pull_request")
                self.assertEqual(run["head_sha"], self.PR_HEAD)
                self.assertEqual(run["head_branch"], self.HEAD_BRANCH)
                self.assertEqual(run["pull_requests"][0]["number"], 100)

    def test_querying_with_merge_commit_reproduces_the_outage(self):
        """The pre-fix behaviour: github.sha (= merge commit) finds nothing."""
        decision = self._verify(self.MERGE_COMMIT)
        self.assertEqual(decision["decision"], "retry")
        self.assertEqual(decision["head_sha"], self.MERGE_COMMIT)
        states = {wf: res["state"] for wf, res in decision["required"].items()}
        self.assertEqual(states, {wf: "retry" for wf in self.REQUIRED})

    def test_merge_commit_query_diagnoses_the_discovery_mismatch(self):
        decision = self._verify(self.MERGE_COMMIT)
        backend_detail = decision["required"][self.BACKEND]["detail"]
        self.assertIn("no workflow run found yet", backend_detail)
        # The green runs ARE visible in the payload — under their own SHA,
        # so the diagnostic must surface that commit prefix.
        self.assertIn(self.PR_HEAD[:12], backend_detail)
        self.assertTrue(
            all(res["state"] != "pass" for res in decision["required"].values()),
            "merge-commit query must never satisfy the gate",
        )

    def test_querying_with_pr_head_sha_discovers_green_runs_and_passes(self):
        decision = self._verify(self.PR_HEAD)
        self.assertEqual(decision["decision"], "pass")
        states = {wf: res["state"] for wf, res in decision["required"].items()}
        self.assertEqual(states, {wf: "pass" for wf in self.REQUIRED})
        self.assertIn("run_id=32941864230", decision["required"][self.BACKEND]["detail"])
        self.assertIn("run_id=32941864282", decision["required"][self.FRONTEND]["detail"])
        self.assertIn("run_id=32941864319", decision["required"][self.DOCKER]["detail"])

    def test_only_an_older_commits_success_never_passes(self):
        runs = [
            dict(run, head_sha=self.OLDER_COMMIT)
            for run in self._fixture_runs()
            if run["path"] in self.REQUIRED
        ]
        decision = self._verify(self.PR_HEAD, runs)
        self.assertEqual(decision["decision"], "retry")

    def test_only_another_branchs_success_never_passes(self):
        runs = [
            dict(run, head_sha=self.OTHER_BRANCH_COMMIT)
            for run in self._fixture_runs()
            if run["path"] in self.REQUIRED
        ]
        decision = self._verify(self.PR_HEAD, runs)
        self.assertEqual(decision["decision"], "retry")
        self.assertNotEqual(
            {res["state"] for res in decision["required"].values()}, {"pass"}
        )

    def test_cli_exit_codes_reproduce_incident_and_fix(self):
        import contextlib
        import io
        import tempfile

        plan = {"required_workflows": list(self.REQUIRED)}
        cases = (
            # (queried SHA, expected exit code) — merge commit retried into
            # timeout pre-fix; PR head commit passes post-fix.
            (self.MERGE_COMMIT, 2),
            (self.PR_HEAD, 0),
        )
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = os.path.join(tmp, "plan.json")
            runs_path = os.path.join(tmp, "runs.json")
            with open(plan_path, "w", encoding="utf-8") as handle:
                json.dump(plan, handle)
            with open(runs_path, "w", encoding="utf-8") as handle:
                json.dump(self._payload(), handle)

            for head_sha, expected in cases:
                with self.subTest(head_sha=head_sha[:12]):
                    stdout = io.StringIO()
                    with contextlib.redirect_stdout(stdout):
                        exit_code = pr_gate.main(
                            [
                                "verify",
                                "--plan",
                                plan_path,
                                "--runs",
                                runs_path,
                                "--head-sha",
                                head_sha,
                            ]
                        )
                    self.assertEqual(exit_code, expected)
                    decision = json.loads(stdout.getvalue())
                    expected_decision = {2: "retry", 0: "pass"}[expected]
                    self.assertEqual(decision["decision"], expected_decision)


if __name__ == "__main__":
    unittest.main()

"""Structural validation of GitHub Actions workflow YAML files (WIQ-V1-010).

Parses every workflow under ``.github/workflows`` with PyYAML and asserts the
invariants the PR Gate relies on. Runs fully offline as part of the unit-test
suite::

    python -m unittest discover -s scripts/ci -v

Note: workflows using an unquoted ``on:`` key parse as Python ``True`` under
PyYAML 1.1 semantics; both spellings are accepted here.
"""

from __future__ import annotations

import glob
import os
import unittest

import yaml

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORKFLOW_DIR = os.path.join(REPO_ROOT, ".github", "workflows")


def load_workflow(filename):
    path = os.path.join(WORKFLOW_DIR, filename)
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def trigger_key(doc):
    for key in ("on", True):
        if key in doc:
            return key
    raise AssertionError(f"workflow {doc.get('name')} defines no triggers")


class WorkflowSyntaxTests(unittest.TestCase):
    """Generic syntax sanity for all workflow files."""

    def test_all_workflow_files_parse_and_have_core_structure(self):
        files = sorted(glob.glob(os.path.join(WORKFLOW_DIR, "*.yml")))
        self.assertTrue(files, "no workflow files found")
        for path in files:
            with self.subTest(workflow=os.path.basename(path)):
                with open(path, "r", encoding="utf-8") as handle:
                    doc = yaml.safe_load(handle)
                self.assertIsInstance(doc, dict)
                self.assertIn("name", doc)
                self.assertIn(trigger_key(doc), doc)
                self.assertIsInstance(doc["jobs"], dict)
                for job_id, job in doc["jobs"].items():
                    self.assertIn("runs-on", job, f"job {job_id} lacks runs-on")
                    steps = job.get("steps")
                    if steps is not None:
                        self.assertIsInstance(steps, list)
                        for step in steps:
                            self.assertTrue(
                                {"run", "uses"} & set(step),
                                f"job {job_id} has a step without run/uses",
                            )


class PrGateWorkflowTests(unittest.TestCase):
    """Invariants that make the PR Gate usable as the required status check."""

    def setUp(self):
        self.doc = load_workflow("pr-gate.yml")

    def test_stable_unique_names(self):
        self.assertEqual(self.doc["name"], "PR Gate")
        job = self.doc["jobs"]["gate"]
        self.assertEqual(job["name"], "PR Gate")
        other_jobs = []
        for filename in ("backend-ci.yml", "frontend-ci.yml", "agent-ci.yml", "docker-ci.yml"):
            other = load_workflow(filename)
            for job_def in other["jobs"].values():
                other_jobs.append(job_def.get("name"))
        self.assertNotIn("PR Gate", other_jobs)

    def test_triggers_on_pull_request_to_main_and_develop(self):
        trigger = self.doc[trigger_key(self.doc)]["pull_request"]
        self.assertEqual(sorted(trigger["branches"]), ["develop", "main"])
        self.assertEqual(
            sorted(trigger["types"]),
            ["opened", "reopened", "synchronize"],
        )

    def test_minimal_read_only_permissions(self):
        # `checks: write` is required so the gate can post its check-run
        # status back to GitHub; with `checks: read` the run stays in
        # "Expected — Waiting for status to be reported" forever (PR #122).
        self.assertEqual(
            self.doc["permissions"],
            {"contents": "read", "checks": "write", "actions": "read"},
        )

    def test_no_secrets_referenced(self):
        raw = open(os.path.join(WORKFLOW_DIR, "pr-gate.yml"), encoding="utf-8").read()
        self.assertNotIn("secrets.", raw)
        self.assertIn("github.token", raw)

    def test_concurrency_superseded_runs_per_pr(self):
        group = self.doc["concurrency"]["group"]
        self.assertIn("github.event.pull_request.number", group)
        self.assertTrue(self.doc["concurrency"]["cancel-in-progress"])

    def test_job_has_timeout(self):
        self.assertLessEqual(self.doc["jobs"]["gate"]["timeout-minutes"], 45)


if __name__ == "__main__":
    unittest.main()

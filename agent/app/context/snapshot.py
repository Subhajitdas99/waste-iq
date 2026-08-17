"""Repository snapshot provider — Phase 1 uses local Git state.

A GitHub API client (Phase 2) can replace this without changing call
sites: the SnapshotProvider protocol only requires fetch() -> str | None.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


class GitSnapshotProvider:
    def __init__(self, root: Path) -> None:
        self._root = root

    def fetch(self) -> str | None:
        try:
            sha = subprocess.run(
                ["git", "-C", str(self._root), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=10,
            ).stdout.strip()
            branch = subprocess.run(
                ["git", "-C", str(self._root), "branch", "--show-current"],
                capture_output=True,
                text=True,
                timeout=10,
            ).stdout.strip()
        except (subprocess.SubprocessError, OSError):
            return None
        if not sha:
            return None
        payload: dict[str, object] = {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "repo_full_name": "local",
            "default_branch": branch or None,
            "branches": [branch] if branch else [],
            "latest_commit_sha": sha,
            "milestones": [],
            "labels": [],
            "issues": {"open": 0, "closed": 0, "wiq_open": 0, "wiq_closed": 0},
            "project": None,
            "roadmap": {"items": []},
        }
        return json.dumps(payload)

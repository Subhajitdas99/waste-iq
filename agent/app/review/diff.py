"""Unified diff parser for pull-request patches."""

from __future__ import annotations

import re

from app.review.review_models import ChangedFile, DiffHunk, DiffLine

_HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")
_FILE_RE = re.compile(r"^diff --git a/(.*) b/(.*)$")


def parse_patch(diff: str | None) -> list[ChangedFile]:
    """Parse a GitHub PR patch into typed ChangedFile objects.

    Handles added / modified / renamed / removed files. Hunks carry exact
    old/new line numbers plus the diff header for downstream reference.
    """
    if not diff:
        return []
    files: list[ChangedFile] = []
    current: ChangedFile | None = None
    current_hunk: DiffHunk | None = None
    old_counter = 0
    new_counter = 0

    def reset_counters(hunk: DiffHunk | None) -> None:
        nonlocal old_counter, new_counter
        if hunk is None:
            return
        old_counter = hunk.old_start
        new_counter = hunk.new_start

    for raw_line in diff.splitlines():
        line = raw_line.rstrip("\n")
        if line.startswith("diff --git "):
            match = _FILE_RE.match(line)
            new_path = match.group(2) if match else ""
            current = ChangedFile(path=new_path or line, status="modified")
            files.append(current)
            current_hunk = None
            continue
        if current is None:
            continue
        if line.startswith("new file mode"):
            current.status = "added"
            continue
        if line.startswith("deleted file mode"):
            current.status = "removed"
            continue
        if line.startswith("rename from ") or line.startswith("rename to "):
            current.status = "renamed"
            continue
        if line.startswith("--- ") or line.startswith("+++ "):
            continue
        if line.startswith("@@"):
            match = _HUNK_RE.match(line)
            if not match:
                continue
            old_start = int(match.group(1))
            old_len = int(match.group(2) or 1)
            new_start = int(match.group(3))
            new_len = int(match.group(4) or 1)
            current_hunk = DiffHunk(
                header=line,
                old_start=old_start,
                old_lines=old_len,
                new_start=new_start,
                new_lines=new_len,
            )
            current.hunks.append(current_hunk)
            reset_counters(current_hunk)
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        if current_hunk is None:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            current_hunk.lines.append(
                DiffLine(kind="added", new_number=new_counter, content=line[1:])
            )
            new_counter += 1
        elif line.startswith("-") and not line.startswith("---"):
            current_hunk.lines.append(
                DiffLine(kind="removed", old_number=old_counter, content=line[1:])
            )
            old_counter += 1
        elif line.startswith("\\ No newline"):
            continue
        else:
            current_hunk.lines.append(
                DiffLine(
                    kind="context",
                    old_number=old_counter,
                    new_number=new_counter,
                    content=line,
                )
            )
            old_counter += 1
            new_counter += 1

    if files:
        for changed_file in files:
            if changed_file.status == "added":
                changed_file.content = "\n".join(content for _, content in changed_file.added_lines)
    return files

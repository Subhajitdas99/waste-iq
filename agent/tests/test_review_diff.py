"""Tests for the unified diff parser."""

from app.review.diff import parse_patch


def test_parse_added_file():
    patch = (
        "diff --git a/backend/app/main.py b/backend/app/main.py\n"
        "new file mode 100644\n"
        "--- /dev/null\n"
        "+++ b/backend/app/main.py\n"
        "@@ -0,0 +1,3 @@\n"
        "+import os\n"
        "+def f():\n"
        "+    return 1\n"
    )
    files = parse_patch(patch)
    assert len(files) == 1
    changed = files[0]
    assert changed.path == "backend/app/main.py"
    assert changed.status == "added"
    assert changed.added_lines == [(1, "import os"), (2, "def f():"), (3, "    return 1")]
    assert changed.content == "import os\ndef f():\n    return 1"
    assert changed.new_content == "import os\ndef f():\n    return 1"
    assert changed.added_line_numbers == {1, 2, 3}


def test_parse_modified_file_with_hunks():
    patch = (
        "diff --git a/src/utils.py b/src/utils.py\n"
        "index 111..222 100644\n"
        "--- a/src/utils.py\n"
        "+++ b/src/utils.py\n"
        "@@ -1,4 +1,5 @@\n"
        " def add(a, b):\n"
        "     return a + b\n"
        "+    print(a)\n"
        " \n"
        " def sub(a, b):\n"
        "@@ -9,2 +10,3 @@\n"
        "-    return a - b\n"
        "+    print(b)\n"
        "+    return a - b\n"
    )
    files = parse_patch(patch)
    assert len(files) == 1
    changed = files[0]
    assert changed.status == "modified"
    assert changed.added_lines == [
        (3, "    print(a)"),
        (10, "    print(b)"),
        (11, "    return a - b"),
    ]
    assert changed.added_line_numbers == {3, 10, 11}
    assert changed.new_content is None or isinstance(changed.new_content, str)
    hunk = changed.hunks[0]
    assert hunk.old_start == 1 and hunk.new_start == 1
    assert hunk.header.startswith("@@ -1,4 +1,5 @@")


def test_parse_removed_file():
    patch = (
        "diff --git a/old.py b/old.py\n"
        "deleted file mode 100644\n"
        "--- a/old.py\n"
        "+++ /dev/null\n"
        "@@ -1,2 +0,0 @@\n"
        "-def gone():\n"
        "-    pass\n"
    )
    files = parse_patch(patch)
    assert files[0].status == "removed"
    assert files[0].added_lines == []


def test_parse_renamed_file():
    patch = (
        "diff --git a/a.py b/b.py\n"
        "similarity index 90%\n"
        "rename from a.py\n"
        "rename to b.py\n"
        "--- a/a.py\n"
        "+++ b/b.py\n"
        "@@ -1 +1 @@\n"
        "-x\n"
        "+y\n"
    )
    files = parse_patch(patch)
    assert files[0].status == "renamed"
    assert files[0].added_lines == [(1, "y")]


def test_parse_empty_diff():
    assert parse_patch(None) == []
    assert parse_patch("") == []
    assert parse_patch("   \n") == []


def test_parse_no_newline_marker_ignored():
    patch = (
        "diff --git a/x.py b/x.py\n"
        "--- a/x.py\n"
        "+++ b/x.py\n"
        "@@ -1 +1 @@\n"
        "-a\n"
        "+b\n"
        "\\ No newline at end of file\n"
    )
    files = parse_patch(patch)
    assert files[0].added_lines == [(1, "b")]
    assert len(files[0].hunks[0].lines) == 2


def test_parse_malformed_lines_are_skipped():
    patch = "diff --git a/x.py b/x.py\n" "@@ garbage @@\n" "+still tracked\n" "-removed\n"
    files = parse_patch(patch)
    assert len(files) == 1
    assert files[0].hunks == []
    assert files[0].added_lines == []

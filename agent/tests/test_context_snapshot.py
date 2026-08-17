import json


from app.context.snapshot import GitSnapshotProvider


def test_git_snapshot_returns_payload(tmp_path, monkeypatch):
    provider = GitSnapshotProvider(tmp_path)

    def fake_run(args, **kwargs):
        class Result:
            stdout = "abc123\n" if "rev-parse" in args else "main\n"
            stderr = ""

        return Result()

    monkeypatch.setattr("app.context.snapshot.subprocess.run", fake_run)
    payload = provider.fetch()
    assert payload is not None
    data = json.loads(payload)
    assert data["latest_commit_sha"] == "abc123"
    assert data["default_branch"] == "main"
    assert data["issues"]["open"] == 0
    assert data["milestones"] == []
    assert "fetched_at" in data


def test_git_snapshot_empty_branch(tmp_path, monkeypatch):
    provider = GitSnapshotProvider(tmp_path)

    def fake_run(args, **kwargs):
        class Result:
            stdout = "" if "branch" in args else "def456\n"
            stderr = ""

        return Result()

    monkeypatch.setattr("app.context.snapshot.subprocess.run", fake_run)
    data = json.loads(provider.fetch())
    assert data["latest_commit_sha"] == "def456"
    assert data["default_branch"] is None
    assert data["branches"] == []


def test_git_snapshot_none_when_no_sha(tmp_path, monkeypatch):
    provider = GitSnapshotProvider(tmp_path)

    def fake_run(args, **kwargs):
        class Result:
            stdout = ""
            stderr = "fatal: not a git repo"

        return Result()

    monkeypatch.setattr("app.context.snapshot.subprocess.run", fake_run)
    assert provider.fetch() is None


def test_git_snapshot_none_on_subprocess_error(tmp_path, monkeypatch):
    provider = GitSnapshotProvider(tmp_path)

    def fake_run(args, **kwargs):
        raise OSError("git not installed")

    monkeypatch.setattr("app.context.snapshot.subprocess.run", fake_run)
    assert provider.fetch() is None

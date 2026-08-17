"""Tests for the Documentation Agent analysis + changelog insertion (Phase 4)."""

import pytest

from app.agents.doc_agent import (
    DocAssistant,
    apply_changelog_insertion,
    build_changelog_entry,
    format_proposal_comment,
    parse_conventional_title,
    patch_branch_name,
)

ANCHOR = "<!-- waste-iq-agent:doc-proposal v1 -->"


def _pr(number=10, title="feat(api): add notifications endpoint"):
    return {"number": number, "title": title, "body": "Adds the endpoint and tests."}


def test_parse_conventional_title_with_scope():
    kind, scope, subject = parse_conventional_title("feat(api): add notifications endpoint")
    assert (kind, scope, subject) == ("feat", "api", "add notifications endpoint")


def test_parse_conventional_title_plain():
    kind, scope, subject = parse_conventional_title("Add notifications endpoint")
    assert kind == ""
    assert scope == ""
    assert subject == "Add notifications endpoint"


@pytest.mark.parametrize(
    "title,expected_section",
    [
        ("feat: new thing", "Added"),
        ("fix: bug thing", "Fixed"),
        ("perf: faster thing", "Changed"),
        ("refactor: tidy thing", "Changed"),
        ("chore: bump deps", "Changed"),
        ("security: harden auth", "Security"),
        ("docs: update readme", "Documented"),
        ("remove: old endpoint", "Removed"),
    ],
)
def test_build_changelog_entry_maps_types(title, expected_section):
    section, entry = build_changelog_entry(1, title, "Summary text here")
    assert section == expected_section
    assert entry is not None
    assert "(#1)" in entry


def test_build_changelog_entry_unknown_type_has_no_entry():
    section, entry = build_changelog_entry(2, "Just a plain title", "Some summary")
    assert section is None
    assert entry is None


def test_build_changelog_entry_short_body_falls_back_to_pr_reference():
    _, entry = build_changelog_entry(3, "feat: tiny", "Yes.")
    assert "See PR #3" in entry


def test_doc_drift_api_route_points_to_api_spec():
    assistant = DocAssistant()
    proposal = assistant.analyze(
        _pr(), changed_files=["backend/app/api/routes/auth.py", "backend/app/services/x.py"]
    )
    paths = [update.doc_path for update in proposal.doc_updates]
    assert "docs/API_SPECIFICATION.md" in paths


def test_doc_drift_models_point_to_database_schema():
    assistant = DocAssistant()
    proposal = assistant.analyze(
        _pr(title="feat(models): add pickup table"), changed_files=["backend/app/models/pickup.py"]
    )
    paths = [update.doc_path for update in proposal.doc_updates]
    assert "docs/DATABASE_SCHEMA.md" in paths


def test_doc_drift_frontend_points_to_readme():
    assistant = DocAssistant()
    proposal = assistant.analyze(
        _pr(title="feat(ui): add dashboard"), changed_files=["frontend/src/pages/Dashboard.tsx"]
    )
    paths = [update.doc_path for update in proposal.doc_updates]
    assert "README.md" in paths


def test_doc_drift_docs_self_changes_are_ignored():
    assistant = DocAssistant()
    proposal = assistant.analyze(
        _pr(title="docs: update readme"), changed_files=["docs/API_SPECIFICATION.md"]
    )
    assert proposal.doc_updates == []
    assert proposal.changelog_section == "Documented"


def test_proposal_comment_contains_anchor_changelog_and_command_hint():
    assistant = DocAssistant()
    proposal = assistant.analyze(_pr(), changed_files=["backend/app/api/routes/auth.py"])
    comment = format_proposal_comment(proposal)
    assert ANCHOR in comment
    assert "### Added" in comment
    assert "/agent docs apply" in comment
    assert "propose-only" in comment
    assert "docs/API_SPECIFICATION.md" in comment


def test_patch_branch_name_is_prefixed_and_stamped():
    name = patch_branch_name(42)
    assert name.startswith("agent/docs-42-")
    assert len(name) == len("agent/docs-42-YYYYMMDD")


def test_apply_changelog_insertion_existing_section():
    changelog = (
        "# Changelog\n\n"
        "## [Unreleased]\n\n"
        "### Added\n\n"
        "- **Old thing (#1)** — whatever.\n\n"
        "### Fixed\n\n"
        "- **Bug (#2)** — fixed.\n\n"
        "## [1.0.0] - 2026-01-01\n"
    )
    new_content, inserted = apply_changelog_insertion(
        changelog, "Fixed", "- **New fix (#9)** — done."
    )
    assert inserted
    assert "- **New fix (#9)** — done." in new_content
    assert (
        new_content.index("### Fixed")
        < new_content.index("New fix")
        < new_content.index("## [1.0.0]")
    )


def test_apply_changelog_insertion_creates_missing_section_in_order():
    changelog = "# Changelog\n\n## [Unreleased]\n\n### Added\n\n- **A (#1)** — a.\n\n"
    new_content, inserted = apply_changelog_insertion(changelog, "Fixed", "- **F (#2)** — f.")
    assert inserted
    assert "### Fixed" in new_content
    assert new_content.index("### Fixed") > new_content.index("### Added")


def test_apply_changelog_insertion_no_unreleased_section():
    changelog = "# Changelog\n\n## [1.0.0] - 2026-01-01\n\n### Added\n"
    new_content, inserted = apply_changelog_insertion(changelog, "Added", "- **X (#1)** — x.")
    assert inserted is False
    assert new_content == changelog

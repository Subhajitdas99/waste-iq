"""Tests for the deterministic review engine."""

from app.review.review_engine import ReviewEngine, language_for_path
from app.review.review_models import (
    ChangedFile,
    ContextReference,
    PullRequestData,
    RepositoryContext,
)


class StubProbe:
    def __init__(self, context=None):
        self._context = context or RepositoryContext()
        self.context_queries = 0
        self.references_retrieved = 0

    def collect(self, changed_files, repo_full_name):
        return self._context


def _file(text, path="backend/app/mod.py", status="added", test=False):
    if test:
        path = "backend/tests/test_mod.py"
    return ChangedFile(path=path, status=status, content=text)


def _review(text, path="backend/app/mod.py", context=None, **kwargs):
    probe = StubProbe(context)
    engine = ReviewEngine(probe, confidence_floor=0.0, **kwargs)
    pr = PullRequestData(number=1, repo_full_name="x/y", files=[_file(text, path=path)])
    findings, _ctx, metrics = engine.review(pr, "x/y")
    return findings, metrics


def _rules(review_result):
    return {(f.rule_id, f.file_path) for f in review_result}


def test_language_detection():
    assert language_for_path("a.py") == "python"
    assert language_for_path("a.jsx") == "react"
    assert language_for_path("a.tsx") == "react"
    assert language_for_path("a.js") == "js"
    assert language_for_path("a.md") == "markdown"
    assert language_for_path("a.unknown") == ""


def test_mutable_default_argument():
    findings, _ = _review("def f(items=[]):\n    return items\n")
    assert ("CORR-PY-DEFAULT-MUTABLE", "backend/app/mod.py") in _rules(findings)


def test_immutable_default_not_flagged():
    findings, _ = _review("def f(items=None):\n    return items\n")
    assert not any(f.rule_id == "CORR-PY-DEFAULT-MUTABLE" for f in findings)


def test_bare_except():
    findings, _ = _review("try:\n    pass\nexcept:\n    pass\n")
    assert ("CORR-PY-EXCEPT", "backend/app/mod.py") in _rules(findings)


def test_typed_except_not_flagged():
    findings, _ = _review("try:\n    pass\nexcept ValueError:\n    pass\n")
    assert not any(f.rule_id == "CORR-PY-EXCEPT" for f in findings)


def test_while_true_without_exit():
    findings, _ = _review('while True:\n    print("x")\n')
    assert ("CORR-PY-WHILE-TRUE", "backend/app/mod.py") in _rules(findings)


def test_while_true_with_break_not_flagged():
    findings, _ = _review("while True:\n    if done:\n        break\n")
    assert not any(f.rule_id == "CORR-PY-WHILE-TRUE" for f in findings)


def test_eq_none():
    findings, _ = _review("if result == None:\n    pass\n")
    assert ("CORR-PY-EQNONE", "backend/app/mod.py") in _rules(findings)


def test_nplus_query_in_loop():
    text = "for item in items:\n    row = db.query(Row).filter(Row.id == item.id).first()\n"
    findings, _ = _review(text)
    assert ("PERF-NPLUS", "backend/app/mod.py") in _rules(findings)


def test_commit_in_loop():
    text = "for item in items:\n    db.commit()\n"
    findings, _ = _review(text)
    assert ("PERF-COMMIT-IN-LOOP", "backend/app/mod.py") in _rules(findings)


def test_string_append_in_loop():
    text = 'for item in items:\n    out += "x"\n'
    findings, _ = _review(text)
    assert ("PERF-STRING-APPEND", "backend/app/mod.py") in _rules(findings)


def test_async_blocking_call():
    text = 'async def route():\n    time.sleep(1)\n    return "ok"\n'
    findings, _ = _review(text)
    assert ("FASTAPI-BLOCKING-CALL", "backend/app/mod.py") in _rules(findings)


def test_async_sync_session():
    text = 'async def route():\n    db = SessionLocal()\n    return "ok"\n'
    findings, _ = _review(text)
    assert ("SA-SYNC-IN-ASYNC", "backend/app/mod.py") in _rules(findings)


def test_async_await_not_flagged():
    text = 'async def route():\n    await work()\n    return "ok"\n'
    findings, _ = _review(text)
    assert not any(f.rule_id == "FASTAPI-BLOCKING-CALL" for f in findings)
    assert not any(f.rule_id == "SA-SYNC-IN-ASYNC" for f in findings)


def test_missing_path_param():
    text = (
        "from fastapi import APIRouter\nrouter = APIRouter()\n"
        '@router.get("/items/{item_id}")\ndef get_item():\n    return "x"\n'
    )
    findings, _ = _review(text)
    assert ("FASTAPI-MISSING-PATH-PARAM", "backend/app/mod.py") in _rules(findings)


def test_present_path_param_not_flagged():
    text = (
        "from fastapi import APIRouter\nrouter = APIRouter()\n"
        '@router.get("/items/{item_id}")\ndef get_item(item_id: int):\n    return item_id\n'
    )
    findings, _ = _review(text)
    assert not any(f.rule_id == "FASTAPI-MISSING-PATH-PARAM" for f in findings)


def test_route_db_import():
    text = (
        "from fastapi import APIRouter\nfrom app.db.session import SessionLocal\n"
        'router = APIRouter()\n@router.get("/x")\ndef x():\n    return "x"\n'
    )
    findings, _ = _review(text)
    assert ("ARCH-ROUTE-DB", "backend/app/mod.py") in _rules(findings)


def test_security_checks():
    findings, _ = _review(
        "data = eval(payload)\n"
        'db.execute(f"SELECT * FROM t WHERE id = {uid}")\n'
        "pickle.loads(data)\n"
        "os.system(cmd)\n"
        'password = "hunter2superlong"\n'
    )
    rules = _rules(findings)
    assert ("SEC-EVAL", "backend/app/mod.py") in rules
    assert ("SEC-SQL-INJECTION", "backend/app/mod.py") in rules
    assert ("SEC-PICKLE", "backend/app/mod.py") in rules
    assert ("SEC-SHELL", "backend/app/mod.py") in rules
    assert ("SEC-HARDCODED-SECRET", "backend/app/mod.py") in rules


def test_react_missing_key():
    text = "const list = items.map((item) => (\n  <li>{item.name}</li>\n));\n"
    findings, _ = _review(text, path="frontend/src/x.jsx")
    assert ("REACT-KEY", "frontend/src/x.jsx") in _rules(findings)


def test_react_key_present_not_flagged():
    text = "const list = items.map((item) => (\n  <li key={item.id}>{item.name}</li>\n));\n"
    findings, _ = _review(text, path="frontend/src/x.jsx")
    assert not any(f.rule_id == "REACT-KEY" for f in findings)


def test_react_key_index():
    text = "const list = items.map((item, index) => <li key={index}>{item}</li>);\n"
    findings, _ = _review(text, path="frontend/src/x.jsx")
    assert ("REACT-KEY-INDEX", "frontend/src/x.jsx") in _rules(findings)


def test_react_target_blank():
    text = '<a href={url} target="_blank">open</a>\n'
    findings, _ = _review(text, path="frontend/src/x.jsx")
    assert ("REACT-TARGET-BLANK", "frontend/src/x.jsx") in _rules(findings)


def test_react_target_blank_with_rel_not_flagged():
    text = '<a href={url} target="_blank" rel="noopener noreferrer">open</a>\n'
    findings, _ = _review(text, path="frontend/src/x.jsx")
    assert not any(f.rule_id == "REACT-TARGET-BLANK" for f in findings)


def test_react_dangerous_html():
    text = "<div dangerouslySetInnerHTML={{ __html: html }} />\n"
    findings, _ = _review(text, path="frontend/src/x.jsx")
    assert ("REACT-DANGEROUS-HTML", "frontend/src/x.jsx") in _rules(findings)


def test_js_loose_equality():
    findings, _ = _review("if (a == b) { return; }\n", path="frontend/src/x.js")
    assert ("CORR-JS-LOOSE-EQ", "frontend/src/x.js") in _rules(findings)


def test_doc_missing_docstring():
    text = "def helper():\n    return 1\n\nclass Widget:\n    pass\n"
    findings, _ = _review(text)
    docs = [f for f in findings if f.rule_id == "DOC-MISSING-DOCSTRING"]
    assert len(docs) == 2


def test_doc_missing_docstring_skips_test_files():
    text = "def helper():\n    return 1\n"
    findings, _ = _review(text, path="backend/tests/test_mod.py")
    assert not any(f.rule_id == "DOC-MISSING-DOCSTRING" for f in findings)


def test_documented_function_not_flagged():
    text = 'def helper():\n    """does things."""\n    return 1\n'
    findings, _ = _review(text)
    assert not any(f.rule_id == "DOC-MISSING-DOCSTRING" for f in findings)


def test_test_gap():
    text = "def f():\n    return 1\n"
    findings, _ = _review(text, path="backend/app/mod.py")
    assert ("TEST-GAP", "backend/app/mod.py") in _rules(findings)


def test_test_gap_satisfied_by_known_test():
    context = RepositoryContext(test_files_known=["backend/tests/test_mod.py"])
    findings, _ = _review("def f():\n    return 1\n", path="backend/app/mod.py", context=context)
    assert not any(f.rule_id == "TEST-GAP" for f in findings)


def test_test_sleep_and_skip():
    text = "import time\n\ndef test_x():\n    time.sleep(2)\n"
    findings, _ = _review(text, path="backend/tests/test_mod.py")
    rules = _rules(findings)
    assert ("TEST-SLEEP", "backend/tests/test_mod.py") in rules


def test_test_skip_marker():
    text = '@pytest.mark.skip(reason="flaky")\ndef test_x():\n    assert True\n'
    findings, _ = _review(text, path="backend/tests/test_mod.py")
    assert ("TEST-SKIP-NEW", "backend/tests/test_mod.py") in _rules(findings)


def test_doc_pr_missing_reference():
    context = RepositoryContext(
        has_context=True,
        related_docs=[ContextReference(path="docs/architecture/other.md", score=0.5)],
    )
    findings, _ = _review("def f():\n    return 1\n", path="backend/app/newmod.py", context=context)
    assert ("DOC-PR-MISSING-REFERENCE", "backend/app/newmod.py") in _rules(findings)


def test_doc_pr_reference_satisfied():
    context = RepositoryContext(
        has_context=True,
        related_docs=[ContextReference(path="docs/architecture/mod.md", score=0.5)],
    )
    findings, _ = _review("def f():\n    return 1\n", path="backend/app/mod.py", context=context)
    assert not any(f.rule_id == "DOC-PR-MISSING-REFERENCE" for f in findings)


def test_doc_pr_rule_needs_docs():
    findings, _ = _review("def f():\n    return 1\n", path="backend/app/mod.py")
    assert not any(f.rule_id == "DOC-PR-MISSING-REFERENCE" for f in findings)


def test_large_file_rule():
    text = "".join(f"line{i}\n" for i in range(50))
    findings, _ = _review(text, path="backend/app/big.py", large_file_threshold=20)
    assert ("ARCH-FILE-LARGE", "backend/app/big.py") in _rules(findings)


def test_findings_have_evidence():
    findings, _ = _review("def f(items=[]):\n    return items\n")
    finding = next(f for f in findings if f.rule_id == "CORR-PY-DEFAULT-MUTABLE")
    assert finding.evidence
    assert finding.evidence[0].kind == "code"
    assert finding.evidence[0].reference == "backend/app/mod.py:1"
    assert finding.snippet is not None
    assert finding.suggestion
    assert finding.confidence > 0


def test_confidence_floor_filters():
    probe = StubProbe()
    engine = ReviewEngine(probe, confidence_floor=0.93)
    pr = PullRequestData(
        number=1,
        repo_full_name="x/y",
        files=[_file("data = eval(payload)\nif x == None:\n    pass\n")],
    )
    findings, _ctx, _metrics = engine.review(pr, "x/y")
    rules = _rules(findings)
    assert ("SEC-EVAL", "backend/app/mod.py") in rules
    assert ("CORR-PY-EQNONE", "backend/app/mod.py") not in rules


def test_max_findings_per_file():
    text = "".join(f"def f{i}():\n    return 1\n" for i in range(10))
    findings, _ = _review(text, path="backend/app/many.py", max_findings_per_file=3)
    file_level = [f for f in findings if f.rule_id == "DOC-MISSING-DOCSTRING"]
    assert len(file_level) == 3


def test_max_files_cap():
    probe = StubProbe()
    engine = ReviewEngine(probe, max_files=1)
    files = [_file("def f():\n    return 1\n", path=f"backend/app/m{i}.py") for i in range(3)]
    pr = PullRequestData(number=1, repo_full_name="x/y", files=files)
    findings, _ctx, metrics = engine.review(pr, "x/y")
    assert metrics.files_analyzed == 1


def test_removed_files_skipped():
    files = [ChangedFile(path="gone.py", status="removed", content=None)]
    pr = PullRequestData(number=1, repo_full_name="x/y", files=files)
    probe = StubProbe()
    engine = ReviewEngine(probe)
    findings, _ctx, metrics = engine.review(pr, "x/y")
    assert metrics.files_analyzed == 0
    assert findings == []


def test_dedupe():
    text = "try:\n    pass\nexcept:\n    pass\n"
    findings, _ = _review(text)
    matches = [f for f in findings if f.rule_id == "CORR-PY-EXCEPT"]
    assert len(matches) == 1


def test_metrics_reported():
    probe = StubProbe()
    probe.context_queries = 4
    probe.references_retrieved = 7
    engine = ReviewEngine(probe)
    pr = PullRequestData(
        number=1,
        repo_full_name="x/y",
        files=[_file("def f(items=[]):\n    return items\n")],
    )
    findings, ctx, metrics = engine.review(pr, "x/y")
    assert metrics.files_analyzed == 1
    assert metrics.added_lines == 2
    assert metrics.context_queries == 4
    assert metrics.references_retrieved == 7
    assert metrics.duration_ms >= 0
    assert ctx.has_context is False


def test_invalid_python_falls_back_to_regex():
    text = "def broken(:\n    pass\n"
    findings, _ = _review(text)
    assert not any(
        f.rule_id
        in (
            "CORR-PY-DEFAULT-MUTABLE",
            "CORR-PY-EXCEPT",
            "CORR-PY-EQNONE",
            "CORR-PY-WHILE-TRUE",
            "FASTAPI-MISSING-PATH-PARAM",
            "SEC-EVAL",
        )
        for f in findings
    )

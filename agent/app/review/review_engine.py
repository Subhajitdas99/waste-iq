"""Deterministic rule engine for PR review.

The engine analyzes the changed files of a pull request (AST + line-level
checks), retrieves repository context through the probe, and emits
evidence-backed ReviewFindings. No LLM calls: every finding is re-derivable
from the diff and the repository index.
"""

from __future__ import annotations

import ast
import re
import time
from pathlib import PurePosixPath

from app.core.config import settings
from app.review.review_context import RepositoryProbe
from app.review.review_models import (
    ChangedFile,
    FindingEvidence,
    PullRequestData,
    RepositoryContext,
    ReviewFinding,
    ReviewMetrics,
    Severity,
)
from app.review.review_prompts import RuleDefinition, get_rule

_LANGUAGE_BY_SUFFIX: dict[str, str] = {
    ".py": "python",
    ".js": "js",
    ".mjs": "js",
    ".cjs": "js",
    ".ts": "ts",
    ".jsx": "react",
    ".tsx": "react",
    ".html": "html",
    ".jinja": "html",
    ".jinja2": "html",
    ".md": "markdown",
    ".rst": "markdown",
    ".sql": "sql",
}

_ROUTE_DECORATOR_RE = re.compile(r"@[\w.]*\.(get|post|put|patch|delete)\(")
_HTTP_PATH_PLACEHOLDER_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
_MAP_EXPR_END_RE = re.compile(r"\)\s*(?:;|,|$|\))")

_SECURITY_CHECKS: list[tuple[str, re.Pattern[str], tuple[str, ...]]] = [
    ("SEC-EVAL", re.compile(r"\beval\s*\(|\bexec\s*\("), ("python",)),
    (
        "SEC-SQL-INJECTION",
        re.compile(r"\b(?:execute|executemany|raw_sql|run_sql)\s*\(\s*(?:f|rf|fr)[\"']"),
        ("python", "sql"),
    ),
    ("SEC-PICKLE", re.compile(r"pickle\.(?:loads|load)\s*\("), ("python",)),
    (
        "SEC-HARDCODED-SECRET",
        re.compile(
            r"(?:api[_-]?key|secret|password|passwd|auth[_-]?token|access[_-]?token)"
            r"[\"']?\s*[:=]\s*[\"'][A-Za-z0-9_\-./+=]{8,}[\"']"
        ),
        ("python", "js", "ts", "react"),
    ),
    ("SEC-SHELL", re.compile(r"shell\s*=\s*True|os\.system\s*\("), ("python", "js")),
    ("SEC-JINJA-XSS", re.compile(r"\|safe\b|mark_safe\s*\("), ("html",)),
]

_REACT_CHECKS: list[tuple[str, re.Pattern[str], tuple[str, ...]]] = [
    ("REACT-KEY-INDEX", re.compile(r"key\s*=\s*\{\s*index\s*\}"), ("react", "js")),
    ("REACT-DANGEROUS-HTML", re.compile(r"dangerouslySetInnerHTML\s*="), ("react",)),
    (
        "REACT-LEGACY-LIFECYCLE",
        re.compile(r"componentWill(?:Mount|ReceiveProps|Update)\s*\("),
        ("react", "js"),
    ),
]

_LINE_CHECKS: list[tuple[str, re.Pattern[str], tuple[str, ...]]] = [
    ("CORR-PY-EQNONE", re.compile(r"(==|!=)\s*None\b"), ("python",)),
    ("CORR-PY-EXCEPT", re.compile(r"except\s*:\s*$"), ("python",)),
    ("CORR-JS-LOOSE-EQ", re.compile(r"[^=!]==[^=]"), ("js", "react", "ts")),
    ("PERF-STRING-APPEND", re.compile(r"([A-Za-z_]\w*)\s*\+=\s*[\"']"), ("python",)),
]

_BLOCKING_CALLS = (
    "time.sleep",
    "requests.",
    "urllib.request",
    "subprocess.",
    "os.system",
    "http.client",
    "socket.",
    "psycopg2.",
)

_SYNC_SA_NAMES = ("Session", "SessionLocal", "sessionmaker", "create_engine")

_HTTP_METHODS = {"get", "post", "put", "patch", "delete"}

_SEVERITY_RANK: dict[Severity, int] = {
    "critical": 5,
    "high": 4,
    "medium": 3,
    "low": 2,
    "info": 1,
}


def language_for_path(path: str) -> str:
    return _LANGUAGE_BY_SUFFIX.get(PurePosixPath(path).suffix.lower(), "")


def is_test_file(path: str) -> bool:
    return "test" in path.lower()


class ReviewEngine:
    def __init__(
        self,
        probe: RepositoryProbe,
        max_files: int | None = None,
        max_lines_per_file: int | None = None,
        max_findings_per_file: int | None = None,
        confidence_floor: float | None = None,
        large_file_threshold: int = 400,
    ) -> None:
        self._probe = probe
        self._max_files = max_files if max_files is not None else settings.agent_review_max_files
        self._max_lines = (
            max_lines_per_file
            if max_lines_per_file is not None
            else settings.agent_review_max_lines_per_file
        )
        self._max_findings = (
            max_findings_per_file
            if max_findings_per_file is not None
            else settings.agent_review_max_findings_per_file
        )
        self._confidence_floor = (
            confidence_floor
            if confidence_floor is not None
            else settings.agent_review_confidence_floor
        )
        self._large_file_threshold = large_file_threshold
        self._adr_refs: list[FindingEvidence] = []
        self._related_files: list[tuple[str, float]] = []
        self._docs_refs: list[FindingEvidence] = []
        self._roadmap_refs: list[FindingEvidence] = []

    def review(
        self, pr: PullRequestData, repo_full_name: str
    ) -> tuple[list[ReviewFinding], RepositoryContext, ReviewMetrics]:
        started = time.perf_counter()
        changed = [f for f in pr.files if f.status in ("added", "modified", "renamed")]
        changed = changed[: self._max_files]
        context = self._probe.collect(changed, repo_full_name)
        self._cache_context(context)

        findings: list[ReviewFinding] = []
        added_lines_total = 0
        for file in changed:
            added = file.added_lines
            if len(added) > self._max_lines:
                added = added[: self._max_lines]
            added_lines_total += len(added)
            findings.extend(self._analyze_file(file, context))

        findings.extend(self._cross_file_checks(changed, context))
        findings = self._dedupe(findings)
        findings.sort(
            key=lambda f: (
                -_SEVERITY_RANK.get(f.severity, 0),
                f.category,
                f.file_path,
                f.start_line,
            )
        )
        metrics = ReviewMetrics(
            files_analyzed=len(changed),
            added_lines=added_lines_total,
            context_queries=self._probe.context_queries,
            references_retrieved=self._probe.references_retrieved,
            duration_ms=int((time.perf_counter() - started) * 1000),
        )
        return findings, context, metrics

    @staticmethod
    def _dedupe(findings: list[ReviewFinding]) -> list[ReviewFinding]:
        seen: set[tuple[str, str, int]] = set()
        unique: list[ReviewFinding] = []
        for finding in findings:
            key = (finding.rule_id, finding.file_path, finding.start_line)
            if key in seen:
                continue
            seen.add(key)
            unique.append(finding)
        return unique

    # ------------------------------------------------------------------
    # per-file analysis
    # ------------------------------------------------------------------
    def _analyze_file(self, file: ChangedFile, context: RepositoryContext) -> list[ReviewFinding]:
        language = language_for_path(file.path)
        if not language:
            return []
        findings: list[ReviewFinding] = []

        react_line_rules = (
            [(rule_id, pattern) for rule_id, pattern, _languages in _REACT_CHECKS]
            if language in ("react", "js")
            else []
        )
        for num, text in file.added_lines:
            for rule_id, pattern, languages in _LINE_CHECKS + _SECURITY_CHECKS:
                if language not in languages:
                    continue
                if pattern.search(text):
                    rule = get_rule(rule_id)
                    if rule is None or rule.base_confidence < self._confidence_floor:
                        continue
                    findings.append(self._emit(rule, file, num, num))
            for rule_id, pattern in react_line_rules:
                if pattern.search(text):
                    rule = get_rule(rule_id)
                    if rule is None or rule.base_confidence < self._confidence_floor:
                        continue
                    findings.append(self._emit(rule, file, num, num))

        if language == "python":
            findings.extend(self._python_ast_checks(file))
            findings.extend(self._python_route_checks(file))
        if language in ("react", "js"):
            findings.extend(self._react_map_checks(file))
            target_blank = self._target_blank_check(file)
            if target_blank is not None:
                findings.append(target_blank)

        return findings[: self._max_findings]

    # ------------------------------------------------------------------
    # python AST checks
    # ------------------------------------------------------------------
    def _python_ast_checks(self, file: ChangedFile) -> list[ReviewFinding]:
        content = file.new_content
        if content is None:
            return []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return []
        added_numbers = file.added_line_numbers
        findings: list[ReviewFinding] = []
        for node in ast.walk(tree):
            lineno = getattr(node, "lineno", None)
            if lineno is None or lineno not in added_numbers:
                continue
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._check_function_node(node, file, findings)
                if isinstance(node, ast.AsyncFunctionDef):
                    self._check_async_blocking(node, file, findings)
            elif isinstance(node, ast.While):
                self._check_while(node, file, findings)
            elif isinstance(node, ast.For):
                self._check_for_loop(node, file, findings)
            elif isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    rule = get_rule("CORR-PY-EXCEPT")
                    if rule:
                        findings.append(self._emit(rule, file, lineno, lineno))
        findings.extend(self._docstring_checks(file, tree, added_numbers))
        findings.extend(self._db_import_check(file, added_numbers))
        return findings

    def _check_function_node(
        self,
        node: ast.AST,
        file: ChangedFile,
        findings: list[ReviewFinding],
    ) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defaults = list(node.args.defaults) + [d for d in node.args.kw_defaults if d]
            for default in defaults:
                if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    rule = get_rule("CORR-PY-DEFAULT-MUTABLE")
                    if rule:
                        findings.append(self._emit(rule, file, node.lineno, node.lineno))
                    break

    def _check_while(
        self, node: ast.While, file: ChangedFile, findings: list[ReviewFinding]
    ) -> None:
        if not (isinstance(node.test, ast.Constant) and node.test.value is True):
            return
        for sub in ast.walk(ast.Module(body=list(node.body) + list(node.orelse), type_ignores=[])):
            if isinstance(sub, (ast.Break, ast.Return, ast.Raise)):
                return
        rule = get_rule("CORR-PY-WHILE-TRUE")
        if rule:
            findings.append(self._emit(rule, file, node.lineno, node.lineno))

    def _check_for_loop(
        self, node: ast.For, file: ChangedFile, findings: list[ReviewFinding]
    ) -> None:
        body = list(node.body) + list(node.orelse)
        nplus_rule = get_rule("PERF-NPLUS")
        commit_rule = get_rule("PERF-COMMIT-IN-LOOP")
        concat_rule = get_rule("PERF-STRING-APPEND")
        lazy_rule = get_rule("SA-LAZY-EAGER")
        loop_var = _loop_target_name(node.target)
        for sub in ast.walk(ast.Module(body=body, type_ignores=[])):
            if not isinstance(sub, ast.Call):
                continue
            call_text = _call_name(sub)
            if call_text is None:
                continue
            if nplus_rule and self._is_query_call(sub):
                if self._not_yet(findings, "PERF-NPLUS", node.lineno):
                    findings.append(self._emit(nplus_rule, file, node.lineno, node.lineno))
            if commit_rule and (call_text == "commit" or call_text.endswith(".commit")):
                if self._not_yet(findings, "PERF-COMMIT-IN-LOOP", sub.lineno):
                    findings.append(self._emit(commit_rule, file, sub.lineno, sub.lineno))
            if (
                lazy_rule
                and loop_var
                and self._loop_var_in_query(sub, loop_var)
                and self._not_yet(findings, "SA-LAZY-EAGER", node.lineno)
            ):
                findings.append(self._emit(lazy_rule, file, node.lineno, node.lineno))
        if concat_rule:
            for sub in ast.walk(ast.Module(body=body, type_ignores=[])):
                if isinstance(sub, ast.AugAssign) and isinstance(sub.op, ast.Add):
                    if self._not_yet(findings, "PERF-STRING-APPEND", sub.lineno):
                        findings.append(self._emit(concat_rule, file, sub.lineno, sub.lineno))
                    break

    def _is_query_call(self, node: ast.Call) -> bool:
        name = _call_name(node)
        if name is None:
            return False
        return name.endswith(".query") or name.endswith(".select") or name == "select"

    def _loop_var_in_query(self, node: ast.Call, loop_var: str) -> bool:
        name = _call_name(node)
        if name is None:
            return False
        if not (name.endswith(".query") or name.endswith(".filter") or name.endswith(".filter_by")):
            return False
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name) and sub.id == loop_var:
                return True
        return False

    def _check_async_blocking(
        self, node: ast.AsyncFunctionDef, file: ChangedFile, findings: list[ReviewFinding]
    ) -> None:
        for sub in ast.walk(node):
            if not isinstance(sub, ast.Call):
                continue
            call_text = _call_name(sub)
            if call_text is None:
                continue
            if call_text.startswith(_BLOCKING_CALLS):
                rule = get_rule("FASTAPI-BLOCKING-CALL")
                if rule and self._not_yet(findings, "FASTAPI-BLOCKING-CALL", node.lineno):
                    findings.append(self._emit(rule, file, node.lineno, node.lineno))
            elif call_text in _SYNC_SA_NAMES or call_text.endswith(".query"):
                rule = get_rule("SA-SYNC-IN-ASYNC")
                if rule and self._not_yet(findings, "SA-SYNC-IN-ASYNC", node.lineno):
                    findings.append(self._emit(rule, file, node.lineno, node.lineno))

    def _docstring_checks(
        self, file: ChangedFile, tree: ast.Module, added_numbers: set[int]
    ) -> list[ReviewFinding]:
        findings: list[ReviewFinding] = []
        rule = get_rule("DOC-MISSING-DOCSTRING")
        if rule is None or is_test_file(file.path):
            return findings
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if node.name.startswith("_"):
                continue
            if node.lineno not in added_numbers:
                continue
            if ast.get_docstring(node) is None:
                findings.append(self._emit(rule, file, node.lineno, node.lineno))
        return findings

    def _db_import_check(self, file: ChangedFile, added_numbers: set[int]) -> list[ReviewFinding]:
        content = file.new_content
        if content is None:
            return []
        if _ROUTE_DECORATOR_RE.search(content) is None:
            return []
        rule = get_rule("ARCH-ROUTE-DB")
        if rule is None:
            return []
        findings: list[ReviewFinding] = []
        for num, text in file.added_lines:
            if re.search(
                r"from\s+[\w.]*\.?(?:db|session|models|sqlalchemy)\b|SessionLocal|create_engine",
                text,
            ):
                findings.append(self._emit(rule, file, num, num))
                break
        return findings

    def _python_route_checks(self, file: ChangedFile) -> list[ReviewFinding]:
        content = file.new_content
        if content is None:
            return []
        findings: list[ReviewFinding] = []
        rule = get_rule("FASTAPI-MISSING-PATH-PARAM")
        if rule is None:
            return findings
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if not _ROUTE_DECORATOR_RE.search(line):
                continue
            path_match = re.search(r"[\"']([^\"']*)[\"']", line)
            if path_match is None:
                continue
            placeholders = _HTTP_PATH_PLACEHOLDER_RE.findall(path_match.group(1))
            if not placeholders:
                continue
            signature = self._next_signature(lines, i + 1)
            if signature is None:
                continue
            missing = [name for name in placeholders if name not in signature]
            for name in missing:
                findings.append(
                    self._emit(
                        rule,
                        file,
                        i + 1,
                        i + 1,
                        extra=f"Path parameter {name!r} is missing from the handler signature.",
                    )
                )
        return findings

    @staticmethod
    def _next_signature(lines: list[str], start: int) -> list[str] | None:
        for line in lines[start:]:
            if line.startswith(("def ", "async def ")):
                match = re.search(r"def\s+\w+\s*\(([^)]*)\)", line)
                return re.findall(r"\b([A-Za-z_]\w*)\b", match.group(1)) if match else []
            if line.startswith(("@", "class ", "def ")):
                return []
        return None

    # ------------------------------------------------------------------
    # react / js checks
    # ------------------------------------------------------------------
    def _react_map_checks(self, file: ChangedFile) -> list[ReviewFinding]:
        content = file.new_content
        if content is None:
            return []
        findings: list[ReviewFinding] = []
        rule = get_rule("REACT-KEY")
        if rule is None:
            return findings
        lines = content.splitlines()
        for i, line in enumerate(lines):
            idx = line.find(".map(")
            if idx < 0:
                continue
            start_line = i + 1
            if start_line not in file.added_line_numbers:
                continue
            span = self._map_span(lines, i, idx)
            if "key=" in span:
                continue
            findings.append(
                self._emit(
                    rule,
                    file,
                    start_line,
                    start_line,
                    extra="Items rendered from .map() must have a stable key.",
                )
            )
        return findings

    @staticmethod
    def _map_span(lines: list[str], line_index: int, idx: int) -> str:
        depth = 0
        opened = False
        parts: list[str] = []
        for i in range(line_index, len(lines)):
            text = lines[i]
            parts.append(text)
            for char in text[idx:]:
                if char == "(":
                    depth += 1
                    opened = True
                elif char == ")":
                    depth -= 1
                    if opened and depth <= 0:
                        return "\n".join(parts)
            idx = 0
        return "\n".join(parts)

    def _target_blank_check(self, file: ChangedFile) -> ReviewFinding | None:
        content = file.new_content
        if content is None:
            return None
        rule = get_rule("REACT-TARGET-BLANK")
        if rule is None:
            return None
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if 'target="_blank"' not in line and "target='_blank'" not in line:
                continue
            target_idx = line.find("target=")
            tag_start = line.rfind("<", 0, target_idx)
            if tag_start < 0:
                tag_start = 0
            tag_end = line.find(">", target_idx)
            tag = line[tag_start:tag_end] if tag_end >= 0 else line[tag_start:]
            if "rel=" not in tag:
                return self._emit(rule, file, i + 1, i + 1)
        return None

    # ------------------------------------------------------------------
    # cross-file checks
    # ------------------------------------------------------------------
    def _cross_file_checks(
        self, changed: list[ChangedFile], context: RepositoryContext
    ) -> list[ReviewFinding]:
        findings: list[ReviewFinding] = []
        findings.extend(self._testing_gap_checks(changed, context))
        findings.extend(self._test_quality_checks(changed))
        findings.extend(self._documentation_gap_checks(changed, context))
        findings.extend(self._large_file_checks(changed))
        return findings

    def _testing_gap_checks(
        self, changed: list[ChangedFile], context: RepositoryContext
    ) -> list[ReviewFinding]:
        rule = get_rule("TEST-GAP")
        if rule is None:
            return []
        changed_tests = {f.path for f in changed if is_test_file(f.path)}
        known = set(context.test_files_known) | changed_tests
        findings: list[ReviewFinding] = []
        for file in changed:
            if is_test_file(file.path):
                continue
            language = language_for_path(file.path)
            if language not in ("python", "js", "ts", "react"):
                continue
            if self._has_matching_test(file.path, known):
                continue
            findings.append(self._emit(rule, file, 1, 1))
        return findings

    @staticmethod
    def _has_matching_test(source_path: str, known_tests: set[str]) -> bool:
        stem = PurePosixPath(source_path).stem
        candidates = {f"test_{stem}", f"{stem}_test"}
        for test_path in known_tests:
            test_stem = PurePosixPath(test_path).stem
            test_lower = test_stem.lower()
            for candidate in candidates:
                if test_lower.startswith(candidate.lower()):
                    return True
        return False

    def _test_quality_checks(self, changed: list[ChangedFile]) -> list[ReviewFinding]:
        findings: list[ReviewFinding] = []
        sleep_rule = get_rule("TEST-SLEEP")
        skip_rule = get_rule("TEST-SKIP-NEW")
        for file in changed:
            if not is_test_file(file.path):
                continue
            for num, text in file.added_lines:
                if sleep_rule and re.search(r"\b(?:time\.)?sleep\s*\(", text):
                    findings.append(self._emit(sleep_rule, file, num, num))
                if skip_rule and re.search(r"@(?:pytest\.mark\.)?skip|pytest\.skip\s*\(", text):
                    findings.append(self._emit(skip_rule, file, num, num))
        return findings

    def _documentation_gap_checks(
        self, changed: list[ChangedFile], context: RepositoryContext
    ) -> list[ReviewFinding]:
        rule = get_rule("DOC-PR-MISSING-REFERENCE")
        if rule is None or rule.base_confidence < self._confidence_floor:
            return []
        if not (context.related_docs or context.related_adrs):
            return []
        known_refs = {
            r.path.lower()
            for r in context.related_docs + context.related_adrs + context.related_roadmap
        }
        findings: list[ReviewFinding] = []
        for file in changed:
            language = language_for_path(file.path)
            if language not in ("python", "js", "ts", "react"):
                continue
            stem = PurePosixPath(file.path).stem.lower()
            if any(stem in ref or ref.endswith(stem) for ref in known_refs):
                continue
            if is_test_file(file.path):
                continue
            findings.append(
                self._emit(
                    rule,
                    file,
                    1,
                    1,
                    extra="No documentation/ADR in the repository index references this change.",
                )
            )
        return findings

    def _large_file_checks(self, changed: list[ChangedFile]) -> list[ReviewFinding]:
        rule = get_rule("ARCH-FILE-LARGE")
        if rule is None or rule.base_confidence < self._confidence_floor:
            return []
        findings: list[ReviewFinding] = []
        for file in changed:
            if len(file.added_lines) > self._large_file_threshold:
                findings.append(self._emit(rule, file, 1, 1))
        return findings

    # ------------------------------------------------------------------
    # finding construction with evidence
    # ------------------------------------------------------------------
    def _emit(
        self,
        rule: RuleDefinition,
        file: ChangedFile,
        start: int,
        end: int,
        extra: str | None = None,
    ) -> ReviewFinding:
        snippet = file.snippet_around(start)
        confidence = rule.base_confidence
        if rule.rule_id in ("PERF-NPLUS", "SA-LAZY-EAGER"):
            confidence = round(rule.base_confidence * 0.85, 2)
        evidence: list[FindingEvidence] = []
        if snippet:
            reference = f"{file.path}:{start}-{end}" if end != start else f"{file.path}:{start}"
            evidence.append(
                FindingEvidence(
                    kind="code",
                    reference=reference,
                    content=snippet,
                    confidence=confidence,
                )
            )
        evidence.extend(self._related_files_evidence(file))
        evidence.extend(self._adr_refs[:3])
        evidence.extend(self._docs_refs[:2])
        related_files = [e.reference for e in evidence if e.kind == "context"]
        related_adrs = [e.reference for e in evidence if e.kind == "adr"]
        explanation = rule.guidance
        if extra:
            explanation = f"{explanation} {extra}"
        return ReviewFinding(
            rule_id=rule.rule_id,
            category=rule.category,
            severity=rule.severity,
            title=rule.title,
            explanation=explanation,
            file_path=file.path,
            start_line=start,
            end_line=end,
            snippet=snippet,
            suggestion=rule.fix,
            confidence=confidence,
            related_adrs=related_adrs,
            related_files=related_files,
            evidence=evidence,
        )

    def _related_files_evidence(self, file: ChangedFile) -> list[FindingEvidence]:
        stem = PurePosixPath(file.path).stem.lower()
        namespace = PurePosixPath(file.path).parts[0] if PurePosixPath(file.path).parts else ""
        result: list[FindingEvidence] = []
        for path, score in self._related_files:
            if path == file.path:
                continue
            if stem in path.lower() or namespace == PurePosixPath(path).parts[0]:
                result.append(FindingEvidence(kind="context", reference=path, confidence=score))
                if len(result) >= 3:
                    break
        return result

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _cache_context(self, context: RepositoryContext) -> None:
        self._adr_refs = [
            FindingEvidence(
                kind="adr",
                reference=f"{r.path}:{r.start_line or 0}",
                confidence=r.score,
            )
            for r in context.related_adrs
        ]
        self._docs_refs = [
            FindingEvidence(kind="doc", reference=r.path, confidence=r.score)
            for r in context.related_docs
        ]
        self._roadmap_refs = [
            FindingEvidence(kind="roadmap", reference=r.path, confidence=r.score)
            for r in context.related_roadmap
        ]
        self._related_files = [
            (r.path, r.score) for r in context.related_files + context.similar_code
        ]

    @staticmethod
    def _not_yet(findings: list[ReviewFinding], rule_id: str, line: int) -> bool:
        return not any(f.rule_id == rule_id and f.start_line == line for f in findings)


def _call_name(node: ast.Call) -> str | None:
    try:
        return ast.unparse(node.func)
    except Exception:  # noqa: BLE001 - unparse is best-effort
        return None


def _loop_target_name(target: ast.AST) -> str | None:
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Tuple):
        for element in target.elts:
            if isinstance(element, ast.Name):
                return element.id
    return None

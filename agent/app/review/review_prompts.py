"""Rules catalog and guidance for the PR Review Agent.

This module is the canonical, human-auditable rule set the review engine
applies. Rules are deterministic (AST + regex + cross-file heuristics) so a
finding can always be re-derived from the diff and the repository context —
no LLM-generated guesses.

Each rule: id, category, severity, a one-line summary, guidance (why it is
flagged and when it matters), and a safe fix template. The engine pairs this
with code + repository evidence and emits a ReviewFinding.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.review.review_models import ReviewCategory, Severity


@dataclass(frozen=True)
class RuleDefinition:
    rule_id: str
    category: ReviewCategory
    severity: Severity
    title: str
    guidance: str
    fix: str
    base_confidence: float
    languages: tuple[str, ...] = ("python",)
    applies_to_test_files: bool = True


RULES: list[RuleDefinition] = [
    # --- Correctness ---
    RuleDefinition(
        rule_id="CORR-PY-DEFAULT-MUTABLE",
        category="correctness",
        severity="medium",
        title="Mutable default argument",
        guidance=(
            "A mutable default ([] / {} / set()) is created once at def time and shared by every "
            "call; mutations leak across calls. Use None + late initialization."
        ),
        fix="def f(items=None):\n    items = [] if items is None else items",
        base_confidence=0.95,
    ),
    RuleDefinition(
        rule_id="CORR-PY-EXCEPT",
        category="correctness",
        severity="medium",
        title="Bare except clause",
        guidance=(
            "A bare `except:` catches even KeyboardInterrupt/SystemExit, masks the real error, and "
            "interferes with proper cleanup. Catch specific exceptions or Exception."
        ),
        fix='except ValueError as exc:\n    logger.warning("invalid value", exc_info=True)',
        base_confidence=0.9,
    ),
    RuleDefinition(
        rule_id="CORR-PY-EQNONE",
        category="correctness",
        severity="low",
        title="Identity check should use `is None`",
        guidance=(
            "`x == None` invokes __eq__ and can return non-bool / array results. Identity is the "
            "defined check for None."
        ),
        fix="if value is None:",
        base_confidence=0.9,
    ),
    RuleDefinition(
        rule_id="CORR-PY-WHILE-TRUE",
        category="correctness",
        severity="medium",
        title="while True loop without a guaranteed exit",
        guidance=(
            "`while True:` with no break/return reachable in the body can hang the service. "
            "Prefer a bounded loop or an explicit condition."
        ),
        fix="while attempt < max_attempts:",
        base_confidence=0.85,
    ),
    RuleDefinition(
        rule_id="CORR-JS-LOOSE-EQ",
        category="correctness",
        severity="low",
        title="Loose equality in JavaScript",
        guidance=(
            "`==` performs type coercion and can silently compare unrelated types; prefer `===` "
            "unless coercion is intended."
        ),
        fix="if (value === expected) {",
        base_confidence=0.5,
        languages=("js", "react", "ts"),
    ),
    # --- Architecture ---
    RuleDefinition(
        rule_id="ARCH-ROUTE-DB",
        category="architecture",
        severity="medium",
        title="Route/controller reaching into the DB layer",
        guidance=(
            "FastAPI routes that import the DB / Session directly bypass the service/repository "
            "layer, coupling HTTP to persistence and making the modules hard to test."
        ),
        fix="Move persistence behind a service/repository and let the route call it.",
        base_confidence=0.8,
    ),
    RuleDefinition(
        rule_id="ARCH-FILE-LARGE",
        category="architecture",
        severity="low",
        title="Very large change in a single file",
        guidance=(
            "Adding this many lines to one file makes it hard to review and maintain; consider "
            "splitting the module."
        ),
        fix="Split the module along its responsibilities.",
        base_confidence=0.75,
    ),
    # --- Security ---
    RuleDefinition(
        rule_id="SEC-EVAL",
        category="security",
        severity="critical",
        title="eval/exec of dynamic input",
        guidance=(
            "eval/exec on non-constant input allows arbitrary code execution. Never evaluate "
            "untrusted data."
        ),
        fix="Replace eval/exec with a safe parser (ast.literal_eval / json / a schema-validated "
        "deserializer).",
        base_confidence=0.95,
    ),
    RuleDefinition(
        rule_id="SEC-SQL-INJECTION",
        category="security",
        severity="high",
        title="SQL built by string interpolation",
        guidance=(
            "f-string/format SQL with user data is injectable. Use bound parameters and the "
            "ORM/SQLAlchemy text() with binds."
        ),
        fix='session.execute(sa.text("SELECT * FROM t WHERE id = :id"), {"id": value})',
        base_confidence=0.9,
    ),
    RuleDefinition(
        rule_id="SEC-PICKLE",
        category="security",
        severity="medium",
        title="Unpickling untrusted data",
        guidance=(
            "pickle.loads on unverified data can execute arbitrary code during unpickling. Only "
            "unpickle data you produced and check integrity."
        ),
        fix="Prefer JSON / a validated schema; if pickle is required, verify a MAC first.",
        base_confidence=0.9,
    ),
    RuleDefinition(
        rule_id="SEC-HARDCODED-SECRET",
        category="security",
        severity="high",
        title="Hardcoded secret or credential",
        guidance=(
            "Secrets in source end up in git history and leak. Move to environment variables or a "
            "secret manager (see ADR on secrets)."
        ),
        fix="Read from settings/env and keep the value out of the repository.",
        base_confidence=0.7,
    ),
    RuleDefinition(
        rule_id="SEC-SHELL",
        category="security",
        severity="high",
        title="Shell invocation with shell=True",
        guidance=(
            "subprocess with shell=True and interpolated input is command-injectable. Pass an "
            "argument list and shell=False."
        ),
        fix='subprocess.run(["cmd", arg], check=True, shell=False)',
        base_confidence=0.9,
    ),
    RuleDefinition(
        rule_id="SEC-JINJA-XSS",
        category="security",
        severity="medium",
        title="Auto-escaped HTML disabled (| safe / mark_safe)",
        guidance=(
            "Disabling HTML auto-escaping on dynamic values enables stored/reflected XSS. Only "
            "mark trusted content safe."
        ),
        fix="Escape the value, or autoescape it and whitelist trusted tags.",
        base_confidence=0.8,
        languages=("html",),
    ),
    # --- Performance ---
    RuleDefinition(
        rule_id="PERF-NPLUS",
        category="performance",
        severity="medium",
        title="Query executed inside a loop (N+1)",
        guidance=(
            "Issuing a query per iteration multiplies DB round-trips. Fetch the whole collection "
            "once and group in memory, or eager-load relationships."
        ),
        fix="Build one query returning all needed rows (or use selectinload/joinedload).",
        base_confidence=0.7,
    ),
    RuleDefinition(
        rule_id="PERF-COMMIT-IN-LOOP",
        category="performance",
        severity="medium",
        title="Transaction commit inside a loop",
        guidance=(
            "Committing per iteration forces a flush-round-trip each time and breaks atomicity. "
            "Commit once after the loop."
        ),
        fix="Move the commit() outside the loop.",
        base_confidence=0.9,
    ),
    RuleDefinition(
        rule_id="PERF-STRING-APPEND",
        category="performance",
        severity="low",
        title="String concatenation in a loop",
        guidance=(
            "Accumulating a string with += in a loop is quadratic. Use a list and ''.join()."
        ),
        fix='parts = [] ... parts.append(x) ... text = "".join(parts)',
        base_confidence=0.6,
    ),
    # --- FastAPI ---
    RuleDefinition(
        rule_id="FASTAPI-MISSING-PATH-PARAM",
        category="fastapi",
        severity="high",
        title="Path placeholder not bound in handler signature",
        guidance=(
            "A route like /items/{item_id} requires the parameter to appear in the handler "
            "signature; otherwise FastAPI raises at request time."
        ),
        fix="def get_item(item_id: int):",
        base_confidence=0.9,
        languages=("python",),
    ),
    RuleDefinition(
        rule_id="FASTAPI-BLOCKING-CALL",
        category="fastapi",
        severity="high",
        title="Blocking call inside an async route",
        guidance=(
            "A synchronous blocking call (requests, time.sleep, sync DB/SQLAlchemy) inside "
            "async def blocks the event loop for the whole app."
        ),
        fix="Run it in a threadpool (fastapi.concurrency.run_in_threadpool) or use async clients.",
        base_confidence=0.8,
        languages=("python",),
    ),
    # --- SQLAlchemy ---
    RuleDefinition(
        rule_id="SA-SYNC-IN-ASYNC",
        category="sqlalchemy",
        severity="high",
        title="Synchronous SQLAlchemy session in async context",
        guidance=(
            "Using a sync Session inside async code blocks the loop. Use the async engine/"
            "AsyncSession (create_async_engine) instead."
        ),
        fix="from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine",
        base_confidence=0.85,
        languages=("python",),
    ),
    RuleDefinition(
        rule_id="SA-LAZY-EAGER",
        category="sqlalchemy",
        severity="medium",
        title="Collection accessed lazily inside a loop",
        guidance=(
            "Accessing a relationship inside a loop triggers lazy loads one query at a time. "
            "Eager-load with selectinload/joinedload."
        ),
        fix="query = select(Model).options(selectinload(Model.children))",
        base_confidence=0.7,
        languages=("python",),
    ),
    # --- React ---
    RuleDefinition(
        rule_id="REACT-KEY",
        category="react",
        severity="medium",
        title="Missing key on list items",
        guidance=(
            "Rendering an array with .map() without a stable key causes reconciliation bugs and "
            "state mixups when the list changes."
        ),
        fix="<li key={payment.id}> ... </li>",
        base_confidence=0.9,
        languages=("react", "js"),
    ),
    RuleDefinition(
        rule_id="REACT-KEY-INDEX",
        category="react",
        severity="low",
        title="Array index used as key",
        guidance=(
            "index keys break identity when items are inserted/removed. Use a stable unique id."
        ),
        fix="key={item.id}",
        base_confidence=0.9,
        languages=("react", "js"),
    ),
    RuleDefinition(
        rule_id="REACT-TARGET-BLANK",
        category="react",
        severity="medium",
        title="target=_blank without rel",
        guidance=(
            "A link opened in a new tab without rel=noopener noreferrer lets the new page access "
            "window.opener, enabling tabnabbing."
        ),
        fix='<a href={url} target="_blank" rel="noopener noreferrer">',
        base_confidence=0.9,
        languages=("react", "js", "html"),
    ),
    RuleDefinition(
        rule_id="REACT-DANGEROUS-HTML",
        category="react",
        severity="high",
        title="dangerouslySetInnerHTML with untrusted content",
        guidance=(
            "Injecting raw HTML renders unescaped user content: a direct XSS sink. Escape or "
            "sanitize server-side."
        ),
        fix="Render text, or sanitize with a vetted HTML sanitizer before use.",
        base_confidence=0.85,
        languages=("react",),
    ),
    RuleDefinition(
        rule_id="REACT-LEGACY-LIFECYCLE",
        category="react",
        severity="low",
        title="Legacy lifecycle method",
        guidance=(
            "componentWillMount / componentWillReceiveProps / componentWillUpdate are deprecated "
            "and unstable with async rendering."
        ),
        fix="Use componentDidMount / getDerivedStateFromProps or hooks.",
        base_confidence=0.8,
        languages=("react", "js"),
    ),
    # --- Testing ---
    RuleDefinition(
        rule_id="TEST-GAP",
        category="testing",
        severity="medium",
        title="Changed module without a matching test",
        guidance=(
            "A production module changed/added in this PR has no test in the PR. Changes to "
            "behavior should ship with coverage."
        ),
        fix="Add/update a test for the module (e.g. tests/<module>_test.py).",
        base_confidence=0.6,
    ),
    RuleDefinition(
        rule_id="TEST-SLEEP",
        category="testing",
        severity="medium",
        title="Sleep in a test (flaky timing)",
        guidance=(
            "time.sleep polling makes tests slow and flaky. Prefer explicit waits, callbacks, or "
            "dependency injection of timing."
        ),
        fix="Inject a clock/waiter, or use a retry with a timeout.",
        base_confidence=0.8,
    ),
    RuleDefinition(
        rule_id="TEST-SKIP-NEW",
        category="testing",
        severity="low",
        title="New skipped test",
        guidance=(
            "A test introduced in this PR is skipped; it is not exercising anything. Restore or "
            "remove it so the suite measures real behavior."
        ),
        fix="Un-skip the test once the behavior is implemented, or remove it.",
        base_confidence=0.8,
    ),
    # --- Documentation ---
    RuleDefinition(
        rule_id="DOC-MISSING-DOCSTRING",
        category="documentation",
        severity="low",
        title="New function/class without a docstring",
        guidance=(
            "New public API surface added in this PR has no docstring; the module's contract is "
            "unreadable from its source."
        ),
        fix="Add a docstring describing purpose, parameters and return.",
        base_confidence=0.7,
        languages=("python",),
    ),
    RuleDefinition(
        rule_id="DOC-PR-MISSING-REFERENCE",
        category="documentation",
        severity="low",
        title="Change not reflected in repository docs",
        guidance=(
            "The repository has documentation (docs/architecture, ADRs, README) but none of it "
            "references this module. Consider updating docs so the change stays crawlable."
        ),
        fix="Update or add a documentation page/ADR entry describing the change.",
        base_confidence=0.45,
    ),
]

_RULE_MAP: dict[str, RuleDefinition] = {rule.rule_id: rule for rule in RULES}


def get_rule(rule_id: str) -> RuleDefinition | None:
    return _RULE_MAP.get(rule_id)


GUIDELINES: dict[str, str] = {
    "correctness": "Focus on bugs the change introduces: ownership, mutable state, error"
    " swallowing, identity vs equality. Always cite the offending line.",
    "architecture": "Check layering (route/service/repository), coupling and decomposition, "
    "consistent with the repository's own structure.",
    "security": "Flag injection, unsafe deserialization, secrets and XSS sinks. No auto-fixes: "
    "only the human can apply them.",
    "performance": "Flag N+1, per-iteration commits and quadratic patterns only when evidence "
    "shows them in the diff.",
    "fastapi": "Flag route signature mismatches, blocking calls in async handlers, and missing "
    "validation against FastAPI's request model.",
    "sqlalchemy": "Flag sync sessions in async contexts, lazy loading in loops, and per-row "
    "commits.",
    "react": "Flag reconciliation hazards (keys), XSS sinks and deprecated lifecycle APIs in JSX.",
    "testing": "Flag missing coverage for changed modules and flaky/disabled tests.",
    "documentation": "Flag undocumented new API surface and changes invisible to the repository's "
    "docs index.",
}

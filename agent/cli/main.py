"""Waste-IQ agent CLI entry point (``wiq``).

Usage examples:

    wiq ask "Explain the dealer approval workflow"
    wiq search "DealerApprovalGate"
    wiq status
    wiq benchmark

The CLI is a thin client: it only calls the existing agent HTTP endpoints and
the existing evaluation benchmark script. It holds no API keys and performs no
repository writes.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from cli import __version__
from cli.client import AgentClient, ClientError
from cli.models import ChatResponse, SearchResponse

DEFAULT_AGENT_URL = "http://127.0.0.1:8000"
AGENT_URL_ENV = "WIQ_AGENT_URL"
AGENT_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_SCRIPT = AGENT_ROOT / "scripts" / "run_evaluation.py"

EXAMPLES = f"""
examples:
  wiq ask "Explain the dealer approval workflow"
  wiq search "DealerApprovalGate"
  wiq status
  wiq benchmark

environment:
  {AGENT_URL_ENV}  Agent base URL (default: {DEFAULT_AGENT_URL})
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wiq",
        description="Thin developer CLI for the Waste-IQ AI Engineering Agent.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EXAMPLES,
    )
    parser.add_argument("--version", action="version", version=f"wiq {__version__}")
    parser.add_argument(
        "--url",
        default=None,
        help=f"Agent base URL (default: ${AGENT_URL_ENV} or {DEFAULT_AGENT_URL})",
    )
    parser.add_argument(
        "--timeout", type=float, default=60.0, help="HTTP timeout in seconds (default: 60)"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    ask = subparsers.add_parser("ask", help="Ask the agent a repository question")
    ask.add_argument("question", help="The question to ask the agent")

    search = subparsers.add_parser("search", help="Search the repository context index")
    search.add_argument("query", help="The search query")
    search.add_argument(
        "--limit", type=int, default=10, help="Maximum number of results (default: 10)"
    )

    subparsers.add_parser("status", help="Show agent health, LLM and context index status")

    benchmark = subparsers.add_parser("benchmark", help="Run the existing evaluation benchmark")
    benchmark.add_argument(
        "--skip-index", action="store_true", help="Passed through to the benchmark script"
    )
    benchmark.add_argument(
        "--repository-root", default=None, help="Passed through to the benchmark script"
    )
    benchmark.add_argument(
        "--baseline", default=None, help="Passed through to the benchmark script"
    )
    benchmark.add_argument("--output", default=None, help="Passed through to the benchmark script")
    benchmark.add_argument(
        "--json-output", default=None, help="Passed through to the benchmark script"
    )
    return parser


def _agent_url() -> str:
    return os.environ.get(AGENT_URL_ENV, DEFAULT_AGENT_URL)


def _make_client(args: argparse.Namespace) -> AgentClient:
    return AgentClient(args.url or _agent_url(), timeout=args.timeout)


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def run_ask(client: AgentClient, question: str) -> None:
    _print_answer(client.chat(question))


def run_search(client: AgentClient, query: str, limit: int) -> None:
    _print_search(client.search(query, limit=limit), query)


def run_status(client: AgentClient) -> int:
    sections: dict[str, dict[str, Any]] = {}
    failures: list[str] = []
    for name, fetch in (
        ("health", client.health),
        ("llm", client.llm_status),
        ("context", client.context_status),
    ):
        try:
            sections[name] = fetch()
        except ClientError as exc:
            failures.append(f"{name}: {exc}")

    if "health" in sections:
        print("Agent Health")
        _print_section(sections["health"], "status", "app", "environment", "github configured")
        print()
    else:
        print("Agent Health   : unreachable")

    if "llm" in sections:
        llm = sections["llm"]
        print("LLM")
        _print_row("enabled", llm.get("enabled", "?"))
        _print_row("provider", llm.get("provider", "?"))
        _print_row("configured", llm.get("configured", "?"))
        _print_row("model", llm.get("model") or "-")
        _print_row("cache", llm.get("cache_backend", "?"))
        _print_row(
            "calls",
            f"{llm.get('total_calls', '?')} (failed {llm.get('failed_calls', '?')})",
        )
        _print_row("avg latency", f"{llm.get('average_latency_ms', '?')} ms")
        print()
    else:
        print("LLM            : unreachable")

    if "context" in sections:
        context = sections["context"]
        print("Context / Index")
        _print_row("files", context.get("indexed_files", "?"))
        _print_row("chunks", context.get("chunk_count", "?"))
        _print_row("embeddings", context.get("embedding_count", "?"))
        _print_row("vectors", context.get("vector_count", "?"))
        _print_row("last indexed", context.get("last_indexed_at") or "-")
        _print_row("repository version", context.get("repository_version") or "-")
        _print_row("is indexing", context.get("is_indexing", "?"))
    else:
        print("Context / Index: unreachable")

    sys.stdout.flush()
    for failure in failures:
        print(f"Warning: {failure}", file=sys.stderr)
    return 1 if failures else 0


def run_benchmark(client: AgentClient, args: argparse.Namespace) -> int:
    if not BENCHMARK_SCRIPT.exists():
        print(f"Error: benchmark script not found at {BENCHMARK_SCRIPT}", file=sys.stderr)
        return 1

    command = [sys.executable, str(BENCHMARK_SCRIPT)]
    if args.skip_index:
        command.append("--skip-index")
    for option in ("--repository-root", "--baseline", "--output", "--json-output"):
        value = getattr(args, option[2:].replace("-", "_"))
        if value:
            command.extend([option, str(value)])

    print(f"Running: {' '.join(command)}")
    try:
        completed = subprocess.run(command, cwd=AGENT_ROOT)
    except OSError as exc:
        print(f"Error: failed to run benchmark: {exc}", file=sys.stderr)
        return 1

    try:
        state = client.evaluation_status()
        _print_benchmark_summary(state)
    except ClientError as exc:
        print(f"Note: cannot fetch benchmark summary from agent: {exc}", file=sys.stderr)
    return completed.returncode


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def _print_answer(response: ChatResponse) -> None:
    print(response.answer)
    print()
    print(f"Intent      : {response.intent}")
    print(f"Confidence  : {response.confidence:.2f}")
    print(f"Provider    : {response.provider or '-'}")
    print(f"Model       : {response.model or '-'}")
    print(f"Cached      : {'yes' if response.cached else 'no'}")
    print(f"Latency     : {response.latency_ms} ms")
    print(f"Grounded    : {'yes' if response.grounded else 'no'}")
    if response.references:
        print()
        print("References")
        for index, reference in enumerate(response.references, start=1):
            location = reference.file_path
            if reference.start_line is not None:
                location += f":{reference.start_line}"
                if reference.end_line is not None:
                    location += f"-{reference.end_line}"
            print(f"  {index}. {location}")


def _print_search(response: SearchResponse, query: str) -> None:
    if not response.results:
        print(f'No results for "{query}".')
        return
    print(f'Top {len(response.results)} results for "{query}":')
    print()
    for index, result in enumerate(response.results, start=1):
        location = f"{result.path}:{result.start_line}-{result.end_line}"
        print(f"  {index:>2}. {result.score:.4f}  {location}")
    print()
    print(f"Total matches: {response.total}")


def _print_section(data: dict[str, Any], *keys: str) -> None:
    for key in keys:
        _print_row(key, data.get(key, "?"))


def _print_row(label: str, value: object) -> None:
    print(f"  {label:<20}: {value}")


def _print_benchmark_summary(state: dict[str, Any]) -> None:
    gates = state.get("gates") or {}
    print("-" * 64)
    print(f"Benchmark version : {state.get('benchmark_version', '?')}")
    print(f"Run id            : {state.get('run_id', '?')}")
    print(f"Overall score     : {state.get('overall_score', '?')}")
    print(f"Cases executed    : {state.get('cases_executed', '?')}")
    print(f"Failures          : {state.get('failures', '?')}")
    print(f"Hallucinations    : {state.get('hallucinations', '?')}")
    print(
        "Gates             : "
        f"search>=90 {_bool(gates.get('repository_search_ge_90'))} | "
        f"grounding=100 {_bool(gates.get('grounding_eq_100'))} | "
        f"halluc=0 {_bool(gates.get('hallucinations_zero'))} | "
        f"overall>=90 {_bool(gates.get('overall_ge_90'))}"
    )
    print(f"VERDICT           : {'PASS' if gates.get('passed') else 'FAIL'}")


def _bool(value: object) -> str:
    if isinstance(value, bool):
        return str(value)
    return str(value) if value is not None else "?"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        client = _make_client(args)
    except ClientError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    try:
        if args.command == "ask":
            run_ask(client, args.question)
            return 0
        if args.command == "search":
            run_search(client, args.query, args.limit)
            return 0
        if args.command == "status":
            return run_status(client)
        if args.command == "benchmark":
            return run_benchmark(client, args)
    except ClientError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        client.close()

    parser.error(f"unknown command: {args.command}")
    return 1

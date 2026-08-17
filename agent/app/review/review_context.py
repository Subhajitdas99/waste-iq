"""Repository context probe for PR review.

Retrieves grounding evidence for a pull request using the Phase 1 Repository
Context Service: related files, documentation, architecture docs, ADRs,
roadmap and similar code. Findings must reference these rather than guess.
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from app.context.di import Container
from app.context.models import ScoredChunk, SearchRequest
from app.review.review_models import ChangedFile, ContextReference, RepositoryContext

_SYMBOL_RE = re.compile(r"(?:def |class |async def )([A-Za-z_][A-Za-z0-9_]*)")
_MODULE_RE = re.compile(r"from [\w.]+ import |import [\w.]+")


class RepositoryProbe:
    """Gathers repository evidence and labels test files the engine knows about."""

    def __init__(self, container: Container, max_references: int = 8, query_limit: int = 8) -> None:
        self._container = container
        self._max_references = max_references
        self._query_limit = query_limit
        self.context_queries = 0
        self.references_retrieved = 0

    def collect(self, changed_files: list[ChangedFile], repo_full_name: str) -> RepositoryContext:
        self.context_queries = 0
        self.references_retrieved = 0
        added_paths = [f.path for f in changed_files if f.status in ("added", "modified")]
        added_text = "\n".join((f.new_content or "") for f in changed_files if f.content)

        related_files = self.find_related_files(added_paths)
        docs = self.find_documentation(repo_full_name, added_paths)
        architecture = self.find_architecture()
        adrs = self.find_adrs()
        roadmap = self.find_roadmap()
        similar = self.find_similar_code(added_text)

        test_files = self._known_test_files()
        has_context = bool(related_files or docs or architecture or adrs or roadmap or similar)

        return RepositoryContext(
            has_context=has_context,
            related_files=related_files,
            related_docs=docs,
            related_adrs=adrs,
            related_roadmap=roadmap,
            similar_code=similar,
            test_files_known=test_files,
        )

    def find_related_files(self, paths: list[str]) -> list[ContextReference]:
        """Files in the same module namespace as the changed files."""
        needles = sorted({f"/{part}/" for path in paths for part in _namespace_parts(path)})[:4]
        if not needles:
            return []
        self.context_queries += 1
        response = self._container.search_service().hybrid_search(
            SearchRequest(
                query=" ".join(path for path in paths)[:200] or "changed file",
                limit=self._query_limit,
                source_types=["code"],
                paths=needles,
            )
        )
        references = [_reference(result) for result in response.results[: self._max_references]]
        self.references_retrieved += len(references)
        return references

    def find_documentation(self, repo_full_name: str, paths: list[str]) -> list[ContextReference]:
        query = " ".join(paths)[:200] or repo_full_name
        self.context_queries += 1
        response = self._container.search_service().hybrid_search(
            SearchRequest(
                query=query,
                limit=self._query_limit,
                source_types=["docs"],
            )
        )
        references = [_reference(result) for result in response.results[: self._max_references]]
        self.references_retrieved += len(references)
        return references

    def find_architecture(self) -> list[ContextReference]:
        self.context_queries += 1
        response = self._container.search_service().hybrid_search(
            SearchRequest(query="architecture design system overview", limit=self._query_limit)
        )
        references = [
            _reference(result)
            for result in response.results[: self._max_references]
            if "architecture" in result.path.lower()
            or "system design" in (result.section_title or "")
        ]
        self.references_retrieved += len(references)
        return references

    def find_adrs(self) -> list[ContextReference]:
        self.context_queries += 1
        response = self._container.search_service().hybrid_search(
            SearchRequest(
                query="architecture decision record", limit=self._query_limit, source_types=["adr"]
            )
        )
        references = [_reference(result) for result in response.results[: self._max_references]]
        self.references_retrieved += len(references)
        return references

    def find_roadmap(self) -> list[ContextReference]:
        self.context_queries += 1
        response = self._container.search_service().hybrid_search(
            SearchRequest(
                query="roadmap milestones priorities",
                limit=self._query_limit,
                source_types=["roadmap"],
            )
        )
        references = [_reference(result) for result in response.results[: self._max_references]]
        self.references_retrieved += len(references)
        return references

    def find_similar_code(self, added_text: str) -> list[ContextReference]:
        query = " ".join(_symbols_of(added_text))[:200]
        if not query:
            return []
        self.context_queries += 1
        response = self._container.search_service().hybrid_search(
            SearchRequest(query=query, limit=self._query_limit, source_types=["code"])
        )
        references = [_reference(result) for result in response.results[: self._max_references]]
        self.references_retrieved += len(references)
        return references

    def _known_test_files(self) -> list[str]:
        try:
            indexed = self._container.store().indexed_files()
        except Exception:  # noqa: BLE001 - an empty repo must not break the probe
            return []
        return [path for path in sorted(indexed) if "test" in path.lower()]


def _namespace_parts(path: str) -> list[str]:
    parts = PurePosixPath(path).parts
    return ["/".join(parts[: i + 1]) for i in range(max(0, len(parts) - 1))]


def _symbols_of(text: str) -> list[str]:
    symbols = _SYMBOL_RE.findall(text)
    imports = _MODULE_RE.findall(text)
    tokens = list(symbols)
    for statement in imports:
        tokens.extend(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*", statement))
    seen: set[str] = set()
    result: list[str] = []
    for token in tokens:
        if token in {"def", "class", "async", "import", "from", "return"}:
            continue
        if token in seen:
            continue
        seen.add(token)
        result.append(token)
    return result[:12]


def _reference(result: ScoredChunk) -> ContextReference:
    return ContextReference(
        path=result.path,
        start_line=result.start_line,
        end_line=result.end_line,
        section_title=result.section_title,
        score=result.score,
        source_type=result.source_type,
    )

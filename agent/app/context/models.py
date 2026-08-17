"""Pydantic models for the Repository Context Service."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

DocumentKind = Literal[
    "architecture", "api", "roadmap", "adr", "feature", "design", "readme", "changelog", "other"
]
SourceType = Literal["code", "docs", "roadmap", "adr", "snapshot", "other"]


class FileMetadata(BaseModel):
    path: str
    language: str
    size: int
    modified_at: float
    checksum: str


class CodeElement(BaseModel):
    kind: str
    name: str
    start_line: int
    end_line: int
    docstring: str | None = None
    detail: dict[str, Any] = Field(default_factory=dict)


class DocumentMetadata(BaseModel):
    path: str
    kind: DocumentKind = "other"
    title: str | None = None
    sections: list[str] = Field(default_factory=list)
    todos: list[str] = Field(default_factory=list)
    milestones: list[str] = Field(default_factory=list)
    adr_ids: list[str] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)


class Chunk(BaseModel):
    chunk_id: str
    file_path: str
    start_line: int
    end_line: int
    section_title: str | None = None
    language: str
    source_type: SourceType = "code"
    content: str
    content_hash: str
    token_estimate: int


class VectorPoint(BaseModel):
    chunk_id: str
    file_path: str
    start_line: int
    end_line: int
    section_title: str | None
    language: str
    source_type: str
    vector: list[float]
    keywords: list[str] = Field(default_factory=list)
    subword_tokens: dict[str, int] = Field(default_factory=dict)
    path_tokens: list[str] = Field(default_factory=list)


class ScoredChunk(BaseModel):
    chunk_id: str
    path: str
    start_line: int
    end_line: int
    section_title: str | None = None
    language: str
    source_type: str
    score: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchFilter(BaseModel):
    languages: list[str] | None = None
    source_types: list[str] | None = None
    paths: list[str] | None = None

    def matches(self, language: str, source_type: str, path: str) -> bool:
        if self.languages and language not in self.languages:
            return False
        if self.source_types and source_type not in self.source_types:
            return False
        if self.paths and not any(path_needle in path for path_needle in self.paths):
            return False
        return True


class SearchRequest(BaseModel):
    query: str
    limit: int = Field(default=10, ge=1, le=50)
    languages: list[str] | None = None
    source_types: list[str] | None = None
    paths: list[str] | None = None
    hybrid: bool = True

    @property
    def filter(self) -> SearchFilter:
        return SearchFilter(
            languages=self.languages, source_types=self.source_types, paths=self.paths
        )


class SearchResponse(BaseModel):
    results: list[ScoredChunk]
    total: int


class MilestoneInfo(BaseModel):
    id: str
    number: int
    title: str
    state: str
    open_issues: int
    closed_issues: int


class LabelInfo(BaseModel):
    id: str
    name: str
    color: str


class IssueCounts(BaseModel):
    open: int
    closed: int
    wiq_open: int
    wiq_closed: int


class ProjectInfo(BaseModel):
    number: int | None = None
    title: str | None = None
    url: str | None = None
    item_count: int = 0


class RoadmapStatusItem(BaseModel):
    title: str
    open_issues: int
    total_issues: int
    progress: float


class RoadmapStatus(BaseModel):
    items: list[RoadmapStatusItem] = Field(default_factory=list)

    @property
    def overall_progress(self) -> float:
        total = sum(item.total_issues for item in self.items) or 0
        closed = sum(item.total_issues - item.open_issues for item in self.items)
        return (closed / total) if total else 0.0


class RepositorySnapshot(BaseModel):
    fetched_at: str
    repo_full_name: str
    default_branch: str | None = None
    branches: list[str] = Field(default_factory=list)
    latest_commit_sha: str | None = None
    milestones: list[MilestoneInfo] = Field(default_factory=list)
    labels: list[LabelInfo] = Field(default_factory=list)
    issues: IssueCounts = IssueCounts(open=0, closed=0, wiq_open=0, wiq_closed=0)
    project: ProjectInfo | None = None
    roadmap: RoadmapStatus = RoadmapStatus()


class ContextStatus(BaseModel):
    indexed_files: int
    chunk_count: int
    embedding_count: int
    vector_count: int
    last_indexed_at: str | None = None
    repository_version: str | None = None
    is_indexing: bool = False


class IndexRunSummary(BaseModel):
    new_files: int
    updated_files: int
    removed_files: int
    chunks_created: int
    chunks_removed: int
    embeddings_created: int
    embeddings_cache_hits: int
    took_seconds: float

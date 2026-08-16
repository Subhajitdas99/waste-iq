"""Wire-contract models for the Waste-IQ agent HTTP API.

These are thin, CLI-side copies of the server response schemas. The CLI never
imports ``app``: it only needs the JSON contract that travels over HTTP.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ChatReference(BaseModel):
    model_config = ConfigDict(extra="ignore")

    file_path: str
    start_line: int | None = None
    end_line: int | None = None


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    intent: str
    answer: str
    confidence: float = 0.0
    references: list[ChatReference] = Field(default_factory=list)
    provider: str = ""
    model: str = ""
    cached: bool = False
    latency_ms: int = 0
    grounded: bool = False
    notes: list[str] = Field(default_factory=list)


class SearchResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    chunk_id: str
    path: str
    start_line: int
    end_line: int
    section_title: str | None = None
    score: float
    source_type: str = "code"


class SearchResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    results: list[SearchResult] = Field(default_factory=list)
    total: int = 0

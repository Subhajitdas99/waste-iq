"""API routes for the Repository Context Service."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_context_service
from app.context.context_service import ContextService
from app.context.models import IndexRunSummary, SearchRequest, SearchResponse

router = APIRouter(prefix="/api/context", tags=["context"])


@router.get("/status", response_model=dict)
def get_status(service: ContextService = Depends(get_context_service)) -> dict:
    return service.status()


@router.post("/reindex", response_model=IndexRunSummary)
def post_reindex(
    reset: bool = Query(default=False),
    service: ContextService = Depends(get_context_service),
) -> IndexRunSummary:
    return service.reindex(reset=reset)


@router.post("/search", response_model=SearchResponse)
def post_search(
    request: SearchRequest,
    service: ContextService = Depends(get_context_service),
) -> SearchResponse:
    return service.search(request)


@router.post("/snapshot", response_model=dict | None)
def post_snapshot(service: ContextService = Depends(get_context_service)) -> dict | None:
    return service.snapshot()


# ----------------------------------------------------------------------
# Debug / introspection endpoints (Phase 2.6 retrieval verification)
# ----------------------------------------------------------------------


@router.get("/debug/index", response_model=dict)
def get_debug_index(
    limit: int = Query(default=100, ge=1, le=2000),
    service: ContextService = Depends(get_context_service),
) -> dict:
    return service.debug_index(limit=limit)


@router.get("/debug/chunks", response_model=dict)
def get_debug_chunks(
    path: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    service: ContextService = Depends(get_context_service),
) -> dict:
    return service.debug_chunks(path=path, limit=limit)


@router.get("/debug/vectors", response_model=dict)
def get_debug_vectors(
    limit: int = Query(default=50, ge=1, le=500),
    service: ContextService = Depends(get_context_service),
) -> dict:
    return service.debug_vectors(limit=limit)


@router.get("/debug/embeddings", response_model=dict)
def get_debug_embeddings(
    path: str | None = Query(default=None),
    service: ContextService = Depends(get_context_service),
) -> dict:
    return service.debug_embeddings(path=path)


@router.post("/debug/search", response_model=dict)
def post_debug_search(
    request: SearchRequest,
    service: ContextService = Depends(get_context_service),
) -> dict:
    return service.debug_search(request)

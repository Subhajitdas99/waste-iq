"""Regression tests: known queries must return the expected repository files.

Phase 2.6 — verifies the fixes for the failed Phase 2.5 retrieval
validation:

* the in-memory vector index is rebuilt from persisted chunks (vector
  store must never be empty on a warm process), and
* hybrid search uses subword-aware keyword scoring (camelCase /
  snake_case identifiers match natural-language queries).
"""

import pytest

from app.context.di import Container
from app.context.models import SearchRequest

DEALER_APPROVAL = "backend/app/services/dealer_approval.py"
CLIENT_TS = "frontend/src/api/client.ts"
REVIEW_ENGINE = "agent/app/review/review_engine.py"

DEALER_APPROVAL_CONTENT = '''"""Dealer approval workflow."""

from dataclasses import dataclass


class AdminDealerApprovalService:
    """Approves or rejects pending dealer accounts."""

    def list_pending_dealers(self, db):
        """List dealers awaiting approval."""
        return []

    def approve_dealer(self, db, dealer_user_id):
        """Approve a dealer account."""
        return True

    def reject_dealer(self, db, dealer_user_id, reason):
        """Reject a dealer account."""
        return False


def is_dealer_approved(db, dealer) -> bool:
    return dealer.status == "approved"
'''

CLIENT_TS_CONTENT = """const REFRESH_TOKEN_STORAGE_KEY = "wasteiq_refresh_token";

export interface AuthSession {
  accessToken?: string | null;
  refreshToken?: string | null;
}

export type RefreshTokenHandler = (refreshToken: string) => Promise<AuthSession>;

let refreshTokenHandler: RefreshTokenHandler | null = null;

export function configureRefreshHandler(handler: RefreshTokenHandler | null): void {
  refreshTokenHandler = handler;
}

function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_STORAGE_KEY);
}

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken || refreshTokenHandler === null) {
    return null;
  }
  return refreshTokenHandler(refreshToken).then((session) => session.accessToken ?? null);
}

export async function apiRequest(path: string): Promise<unknown> {
  let token = getRefreshToken();
  if (!token) {
    token = await refreshAccessToken();
  }
  const response = await fetch(`/api${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (response.status === 401) {
    const next = await refreshAccessToken();
    if (next) {
      return fetch(`/api${path}`, {
        headers: { Authorization: `Bearer ${next}` },
      });
    }
  }
  return response.json();
}
"""

REVIEW_ENGINE_CONTENT = '''"""Review engine — runs rule-based review over pull request diffs."""

from __future__ import annotations

import re


class ReviewEngine:
    """Applies review rules to changed files and collects findings."""

    def run(self, changed_files, diff_text):
        """Execute all rules against the provided diff."""
        findings = []
        for rule in self._rules():
            findings.extend(rule(diff_text))
        return findings

    def _rules(self):
        return [self._rule_no_debug_print, self._rule_no_merge_conflicts]

    def _rule_no_debug_print(self, text):
        return []

    def _rule_no_merge_conflicts(self, text):
        return []
'''

MARKETPLACE_DISTRACTOR = '''"""Marketplace service."""

from dataclasses import dataclass


@dataclass
class Listing:
    id: int
    dealer_id: int
    price: float


class MarketplaceService:
    def list_listings(self, db):
        return []

    def create_listing(self, db, dealer_id, price):
        return Listing(id=1, dealer_id=dealer_id, price=price)
'''

REVIEW_DOC_DISTRACTOR = """# PR Review Agent

The review agent reviews pull requests. The review process uses the review
engine internally. Review findings include review comments. The review agent
runs review rules. Every review produces a review report. The reviewer
reviews code. Reviews are stored in the review session. The review engine
scans review diffs.
"""

TOKEN_DOC_DISTRACTOR = """# Authentication

The platform uses tokens for authentication. Access tokens expire. A refresh
token can be exchanged for a new access token. Token rotation refreshes the
token. Tokens must be stored securely. Refresh token storage uses a token
store. Token refresh happens when the token is expired.
"""


@pytest.fixture
def indexed_container(tmp_path, clean_context_db):
    from app.db.session import SessionLocal

    def write(rel: str, content: str) -> None:
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    write(DEALER_APPROVAL, DEALER_APPROVAL_CONTENT)
    write(CLIENT_TS, CLIENT_TS_CONTENT)
    write(REVIEW_ENGINE, REVIEW_ENGINE_CONTENT)
    write("backend/app/services/marketplace.py", MARKETPLACE_DISTRACTOR)
    write("docs/architecture/PR_REVIEW_AGENT.md", REVIEW_DOC_DISTRACTOR)
    write("docs/authentication.md", TOKEN_DOC_DISTRACTOR)

    container = Container(
        SessionLocal,
        repository_root=tmp_path,
        min_tokens=50,
        max_tokens=500,
    )
    container.pipeline().run()
    return container


def _paths(response) -> list[str]:
    return [result.path for result in response.results]


def test_vector_index_populated_after_reindex(indexed_container):
    status = indexed_container.status()
    assert status["chunk_count"] > 0
    assert status["vector_count"] == status["chunk_count"]


def test_query_dealer_approval_returns_dealer_approval(indexed_container):
    service = indexed_container.search_service()
    response = service.hybrid_search(SearchRequest(query="dealer approval", limit=5))
    assert response.total >= 1
    assert DEALER_APPROVAL in _paths(response)[:5]


def test_query_refresh_token_returns_client_ts(indexed_container):
    service = indexed_container.search_service()
    response = service.hybrid_search(SearchRequest(query="refresh token", limit=5))
    assert response.total >= 1
    assert CLIENT_TS in _paths(response)[:5]


def test_query_review_engine_returns_review_engine(indexed_container):
    service = indexed_container.search_service()
    response = service.hybrid_search(SearchRequest(query="review_engine", limit=5))
    assert response.total >= 1
    assert REVIEW_ENGINE in _paths(response)[:5]


def test_restart_rebuilds_vector_index_from_persistence(tmp_path, indexed_container):
    """A fresh process (new container, unchanged repo) must serve search.

    Regression for the Phase 2.5 bug: the in-memory vector store started
    empty on restart (vector_count == 0) so every search returned nothing.
    """
    from app.db.session import SessionLocal

    fresh = Container(
        SessionLocal,
        repository_root=tmp_path,
        min_tokens=50,
        max_tokens=500,
    )
    summary = fresh.pipeline().run()
    assert summary.new_files == 0
    assert fresh.status()["vector_count"] == fresh.status()["chunk_count"]
    assert fresh.status()["vector_count"] > 0

    response = fresh.search_service().hybrid_search(SearchRequest(query="review_engine", limit=5))
    assert REVIEW_ENGINE in _paths(response)[:5]


def test_updated_file_vectors_stay_consistent(tmp_path, indexed_container):
    (tmp_path / REVIEW_ENGINE).write_text(
        REVIEW_ENGINE_CONTENT + "\n# extra trailing comment\n",
        encoding="utf-8",
    )
    summary = indexed_container.pipeline().run()
    assert summary.updated_files >= 1
    status = indexed_container.status()
    assert status["vector_count"] == status["chunk_count"]

    response = indexed_container.search_service().hybrid_search(
        SearchRequest(query="review_engine", limit=5)
    )
    assert REVIEW_ENGINE in _paths(response)[:5]


def test_language_filter_still_applies(indexed_container):
    service = indexed_container.search_service()
    response = service.hybrid_search(SearchRequest(query="review", limit=10, languages=["py"]))
    assert response.total >= 1
    assert all(result.language == "py" for result in response.results)


def test_source_type_filter_still_applies(indexed_container):
    service = indexed_container.search_service()
    response = service.hybrid_search(SearchRequest(query="token", limit=10, source_types=["docs"]))
    assert response.total >= 1
    assert all(result.source_type == "docs" for result in response.results)


def test_empty_query_returns_nothing(indexed_container):
    response = indexed_container.search_service().hybrid_search(SearchRequest(query="", limit=5))
    assert response.total == 0

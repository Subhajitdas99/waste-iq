import os
import tempfile

_tmp_db = tempfile.NamedTemporaryFile(prefix="agent_test_", suffix=".db", delete=False)
_tmp_repo = tempfile.mkdtemp(prefix="agent_test_repo_")
os.environ["AGENT_DATABASE_URL"] = f"sqlite:///{_tmp_db.name}"
os.environ["AGENT_WEBHOOK_SECRET"] = "test-webhook-secret"
os.environ["AGENT_GITHUB_APP_ID"] = "12345"
os.environ["AGENT_GITHUB_INSTALLATION_ID"] = "999"
os.environ["AGENT_ADMIN_API_TOKEN"] = "test-admin-token"
os.environ["AGENT_ENVIRONMENT"] = "test"
os.environ["AGENT_LOG_LEVEL"] = "CRITICAL"
os.environ["AGENT_GITHUB_APP_PRIVATE_KEY"] = (
    "-----BEGIN RSA PRIVATE KEY-----\nFAKE_PRIVATE_KEY\n-----END RSA PRIVATE KEY-----\n"
)
os.environ["AGENT_INDEX_ON_STARTUP"] = "false"
os.environ["AGENT_OTEL_ENABLED"] = "false"
os.environ["AGENT_REPOSITORY_ROOT"] = _tmp_repo
os.environ["AGENT_LLM_CACHE_BACKEND"] = "memory"
# Pin AI settings so a developer's real .env can never leak into the suite
# (env vars take precedence over the dotenv file in pydantic-settings).
os.environ["AGENT_LLM_PROVIDER"] = "mock"
os.environ["AGENT_LLM_MODEL"] = ""
os.environ["AGENT_LLM_API_KEY"] = ""
os.environ["AGENT_LLM_BASE_URL"] = ""
os.environ["AGENT_OPENAI_API_KEY"] = ""
os.environ["AGENT_ANTHROPIC_API_KEY"] = ""
os.environ["AGENT_GOOGLE_API_KEY"] = ""
os.environ["AGENT_OPENROUTER_API_KEY"] = ""
os.environ["AGENT_OPENROUTER_HTTP_REFERER"] = ""
os.environ["AGENT_OPENROUTER_APP_NAME"] = ""
os.environ["AGENT_EMBEDDING_PROVIDER"] = "memory"
os.environ["AGENT_CONTEXT_ROOTS"] = "backend,frontend,docs,.github"
os.environ["AGENT_ISSUE_AUTO_RUN"] = "false"
os.environ["AGENT_ISSUE_COMMENTS_ENABLED"] = "false"
os.environ["AGENT_DOCS_AUTO_RUN"] = "false"
os.environ["AGENT_DOCS_COMMENTS_ENABLED"] = "false"
os.environ["AGENT_DOCS_PATCH_PR_ENABLED"] = "false"

from pathlib import Path  # noqa: E402

_repo = Path(_tmp_repo)
(_repo / "src").mkdir(parents=True, exist_ok=True)
(_repo / "src" / "utils.py").write_text(
    "def add(a, b):\n    return a + b\n\nclass Calculator:\n    def multiply(self, a, b):\n"
    "        return a * b\n"
)
(_repo / "README.md").write_text("# Waste IQ\n\n## Architecture\nThe system uses FastAPI.\n")

import pytest  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _init_database() -> None:
    from app.db.session import init_db

    init_db()


@pytest.fixture(autouse=True)
def _reset_container():
    from app.api import dependencies

    dependencies._container = None  # noqa: SLF001
    dependencies._review_service = None  # noqa: SLF001
    dependencies._llm_service = None  # noqa: SLF001
    dependencies._chat_service = None  # noqa: SLF001


@pytest.fixture
def clean_context_db():
    from sqlalchemy import delete

    from app.db.models import (
        ChunkRecord,
        EmbeddingCacheEntry,
        IndexedFile,
        RepositorySnapshotEntry,
    )
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        for model in (
            ChunkRecord,
            EmbeddingCacheEntry,
            IndexedFile,
            RepositorySnapshotEntry,
        ):
            db.execute(delete(model))
        db.commit()
    finally:
        db.close()


@pytest.fixture
def clean_review_db():
    from sqlalchemy import delete

    from app.db.models import ReviewEvidenceRow, ReviewFindingRow, ReviewSession
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        for model in (ReviewEvidenceRow, ReviewFindingRow, ReviewSession):
            db.execute(delete(model))
        db.commit()
    finally:
        db.close()


@pytest.fixture
def noop_probe():
    """A probe that never touches the repository index (deterministic rules)."""

    class _NoopProbe:
        context_queries = 0
        references_retrieved = 0

        def collect(self, changed_files, repo_full_name):
            from app.review.review_models import RepositoryContext

            return RepositoryContext()

    return _NoopProbe()


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client

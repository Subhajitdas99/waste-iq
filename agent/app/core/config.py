import json
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT_DEFAULT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "Waste-IQ AI Agent"
    environment: Literal["development", "test", "staging", "production"] = Field(
        default="development",
        validation_alias=AliasChoices("AGENT_ENVIRONMENT", "ENVIRONMENT"),
    )
    log_level: str = Field(
        default="INFO", validation_alias=AliasChoices("AGENT_LOG_LEVEL", "LOG_LEVEL")
    )

    agent_github_app_id: str = ""
    agent_github_app_private_key: str = ""
    agent_github_app_private_key_path: str | None = None
    agent_github_installation_id: int = 0

    @field_validator("agent_github_installation_id", mode="before")
    @classmethod
    def _empty_installation_id_means_unset(cls, value: object) -> object:
        """Treat the documented empty ``AGENT_GITHUB_INSTALLATION_ID=`` as 0."""
        if value == "":
            return 0
        return value

    agent_webhook_secret: str = ""

    agent_database_url: str = f"sqlite:///{BASE_DIR / 'agent.db'}"
    agent_admin_api_token: str | None = None

    # --- Repository Context Service (Phase 1) ---
    agent_repository_root: Path = REPOSITORY_ROOT_DEFAULT
    # NoDecode: env/dotenv values arrive as raw strings so both the documented
    # comma-separated format and JSON arrays can be parsed by the validator below.
    agent_context_roots: Annotated[list[str], NoDecode] = [
        "backend",
        "frontend",
        "docs",
        ".github",
    ]

    @field_validator("agent_context_roots", mode="before")
    @classmethod
    def _parse_context_roots(cls, value: object) -> object:
        """Accept ``backend,frontend,docs`` (dotenv) or JSON arrays."""
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("["):
                return json.loads(text)
            return [part.strip() for part in text.split(",") if part.strip()]
        return value

    agent_ignored_dirs: list[str] = [
        ".git",
        "node_modules",
        "dist",
        "build",
        "coverage",
        "__pycache__",
        ".venv",
        "venv",
        "env",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".agents",
        "uploads",
        "media",
        "secrets",
        "evaluation",
    ]
    agent_ignored_files: list[str] = [
        ".env",
        ".env.example",
        "*.pem",
        "*.key",
        "credentials.json",
        "service-account.json",
        "*.db",
        "*.sqlite",
        "*.sqlite3",
        "*.pyc",
        "*.pyo",
    ]

    agent_chunk_min_tokens: int = 450
    agent_chunk_max_tokens: int = 1000

    agent_vector_store: Literal["qdrant", "pgvector", "memory"] = "memory"
    agent_qdrant_url: str | None = None
    agent_qdrant_local_path: str | None = None
    agent_qdrant_collection: str = "waste_iq_agent"

    agent_embedding_provider: Literal["openai", "ollama", "memory"] = "memory"
    agent_embedding_dimension: int = 384
    agent_openai_api_key: str | None = None
    agent_openai_embedding_model: str = "text-embedding-3-small"
    agent_openai_embedding_base_url: str = "https://api.openai.com/v1"
    agent_ollama_url: str = "http://localhost:11434"
    agent_ollama_embedding_model: str = "nomic-embed-text"

    agent_github_project_number: int | None = None

    # --- Observability ---
    agent_enable_prometheus: bool = True
    agent_enable_request_id: bool = True
    agent_otel_enabled: bool = False

    # --- Background indexer ---
    agent_index_on_startup: bool = True
    agent_index_startup_delay_seconds: float = 0.0
    agent_embed_batch_size: int = 32

    # --- PR Review Agent (Phase 2) ---
    agent_review_enabled: bool = True
    agent_review_auto_run: bool = True
    agent_review_fixture_repo: str = "waste-iq/demo"
    agent_review_engine_version: str = "2.0.0"
    agent_review_max_files: int = 100
    agent_review_max_lines_per_file: int = 3000
    agent_review_max_findings_per_file: int = 25
    agent_review_confidence_floor: float = 0.4
    agent_review_find_pull_request: bool = True
    agent_github_api_base_url: str = "https://api.github.com"

    # --- Issue Assistant (Phase 3) ---
    agent_issue_enabled: bool = True
    agent_issue_auto_run: bool = False
    agent_issue_comments_enabled: bool = False
    agent_issue_duplicate_threshold: float = 0.35
    agent_issue_max_duplicates: int = 3

    # --- Documentation Agent (Phase 4) ---
    agent_docs_enabled: bool = True
    agent_docs_auto_run: bool = False
    agent_docs_comments_enabled: bool = False
    agent_docs_patch_pr_enabled: bool = False
    agent_docs_default_base: str = "develop"
    agent_docs_changelog_path: str = "CHANGELOG.md"

    # --- Developer Chat Assistant (Phase 5) ---
    agent_chat_enabled: bool = True
    agent_chat_max_turns: int = 10
    agent_chat_retrieval_limit: int = 6
    agent_chat_max_question_chars: int = 4000
    agent_chat_repository: str = "waste-iq"

    # --- Evaluation & Benchmark Framework (Phase 4.5) ---
    agent_benchmark_version: str = "1.0.0"
    agent_evaluation_state_path: str = str(BASE_DIR / "evaluation_state.json")

    # --- LLM Intelligence Layer (Phase 2.5) ---
    agent_llm_enabled: bool = True
    agent_llm_provider: Literal["openai", "anthropic", "google", "ollama", "openrouter", "mock"] = (
        "mock"
    )
    agent_llm_model: str = ""
    agent_llm_api_key: str | None = None
    agent_anthropic_api_key: str | None = None
    agent_google_api_key: str | None = None
    agent_llm_base_url: str | None = None
    agent_llm_timeout_seconds: float = 60.0
    agent_llm_max_retries: int = 2
    agent_llm_retry_backoff_seconds: float = 0.5
    agent_llm_max_input_tokens: int = 14000
    agent_llm_max_output_tokens: int = 1500
    agent_llm_temperature: float = 0.0
    agent_llm_cache_enabled: bool = True
    agent_llm_cache_backend: Literal["memory", "sqlite", "redis"] = "sqlite"
    agent_llm_cache_ttl_seconds: int = 3600
    agent_llm_cache_path: str = str(BASE_DIR / "agent_llm_cache.db")
    agent_llm_redis_url: str | None = None
    agent_llm_rate_limit_per_minute: int = 120
    agent_llm_cost_input_per_1m: float = 2.5
    agent_llm_cost_output_per_1m: float = 10.0

    # --- OpenRouter provider (Phase 5.1) ---
    agent_openrouter_api_key: str | None = None
    agent_openrouter_base_url: str = "https://openrouter.ai/api/v1"
    agent_openrouter_http_referer: str | None = None
    agent_openrouter_app_name: str | None = None

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def github_private_key(self) -> str | None:
        if self.agent_github_app_private_key:
            return self.agent_github_app_private_key
        if self.agent_github_app_private_key_path:
            path = Path(self.agent_github_app_private_key_path)
            if path.exists():
                return path.read_text()
        return None

    @property
    def github_configured(self) -> bool:
        return bool(
            self.agent_github_app_id
            and self.agent_github_installation_id
            and self.github_private_key
            and self.agent_webhook_secret
        )

    @property
    def context_root_paths(self) -> list[Path]:
        return [self.agent_repository_root / root for root in self.agent_context_roots]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

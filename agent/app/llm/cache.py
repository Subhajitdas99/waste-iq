"""Prompt/response caching with a pluggable backend.

Identical prompts (request bytes including provider+model) hash to the same
key, so identical requests never hit the provider twice. Backends: in-memory
(default safe), SQLite (durable fallback), and Redis (best-effort, requires
the optional `redis` package).
"""

from __future__ import annotations

import hashlib
import logging
import sqlite3
import threading
import time
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class CacheBackend(Protocol):
    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str, ttl: int | None = None) -> None: ...
    def delete(self, key: str) -> None: ...
    def ping(self) -> bool: ...


class MemoryCache:
    """Thread-safe in-memory cache with optional TTL."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, str]] = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> str | None:
        with self._lock:
            item = self._store.get(key)
            if item is None:
                return None
            expires, value = item
            if expires and expires < time.monotonic():
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: str, ttl: int | None = None) -> None:
        expires = 0.0 if ttl is None else time.monotonic() + ttl
        with self._lock:
            self._store[key] = (expires, value)

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def ping(self) -> bool:
        return True

    def __len__(self) -> int:
        return len(self._store)


class SqliteCache:
    """SQLite-backed cache. Path may be ':memory:' for tests."""

    def __init__(self, path: str, ttl: int | None = None) -> None:
        self._path = path
        self._default_ttl = ttl
        self._lock = threading.RLock()
        self._shared: sqlite3.Connection | None = None
        if path == ":memory:":
            self._shared = sqlite3.connect(":memory:")
            self._init(self._shared)
        else:
            import os

            parent = os.path.dirname(path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            self._init()

    def _connect(self) -> sqlite3.Connection:
        if self._shared is not None:
            return self._shared
        conn = sqlite3.connect(self._path, timeout=5.0)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init(self, conn: sqlite3.Connection | None = None) -> None:
        conn = conn or self._connect()
        try:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS llm_cache (key TEXT PRIMARY KEY, value TEXT NOT NULL, "
                "expires REAL NOT NULL)"
            )
            conn.commit()
        finally:
            if self._shared is None:
                conn.close()

    def _close(self, conn: sqlite3.Connection) -> None:
        if self._shared is None:
            conn.close()

    def get(self, key: str) -> str | None:
        with self._lock:
            conn = self._connect()
            try:
                row = conn.execute(
                    "SELECT value, expires FROM llm_cache WHERE key = ?", (key,)
                ).fetchone()
            finally:
                self._close(conn)
            if row is None:
                return None
            value, expires = row
            if expires and expires < time.time():
                self.delete(key)
                return None
            return value

    def set(self, key: str, value: str, ttl: int | None = None) -> None:
        ttl = self._default_ttl if ttl is None else ttl
        expires = 0.0 if ttl is None else time.time() + ttl
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    "INSERT INTO llm_cache (key, value, expires) VALUES (?, ?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET "
                    "value = excluded.value, expires = excluded.expires",
                    (key, value, expires),
                )
                conn.commit()
            finally:
                self._close(conn)

    def delete(self, key: str) -> None:
        with self._lock:
            conn = self._connect()
            try:
                conn.execute("DELETE FROM llm_cache WHERE key = ?", (key,))
                conn.commit()
            finally:
                self._close(conn)

    def ping(self) -> bool:
        try:
            conn = self._connect()
            conn.execute("SELECT 1 FROM llm_cache LIMIT 1")
            self._close(conn)
            return True
        except sqlite3.Error:  # pragma: no cover - defensive
            logger.warning("sqlite cache unavailable", exc_info=True)
            return False


class RedisCache:
    """Redis-backed cache. Requires the optional `redis` package."""

    def __init__(self, url: str) -> None:
        try:
            import redis  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - depends on optional dep
            raise RuntimeError("redis package is not installed") from exc
        self._client: Any = redis.Redis.from_url(url, decode_responses=True)

    def get(self, key: str) -> str | None:
        value = self._client.get(key)
        return value

    def set(self, key: str, value: str, ttl: int | None = None) -> None:
        self._client.set(key, value, ex=ttl)

    def delete(self, key: str) -> None:
        self._client.delete(key)

    def ping(self) -> bool:
        return bool(self._client.ping())


def build_cache(settings) -> CacheBackend:
    """Select the cache backend from configuration."""
    backend = settings.agent_llm_cache_backend
    if backend == "memory":
        return MemoryCache()
    cache: CacheBackend
    if backend == "redis":
        if not settings.agent_llm_redis_url:
            logger.warning("redis cache requested but AGENT_LLM_REDIS_URL is empty; using memory")
            return MemoryCache()
        try:
            cache = RedisCache(settings.agent_llm_redis_url)
            if cache.ping():
                return cache
        except RuntimeError:  # pragma: no cover - redis optional
            logger.warning("redis cache unavailable; falling back to memory", exc_info=True)
        return MemoryCache()
    try:
        cache = SqliteCache(settings.agent_llm_cache_path)
    except sqlite3.Error:  # pragma: no cover - defensive
        logger.warning("sqlite cache unavailable; falling back to memory", exc_info=True)
        return MemoryCache()
    return cache


def hash_request(provider: str, model: str, system_prompt: str, user_prompt: str) -> str:
    """Stable hash key for a full prompt."""

    def _normalize(text: str) -> str:
        return " ".join(text.split())

    key = "\x1f".join([provider, model, _normalize(system_prompt), _normalize(user_prompt)])
    return hashlib.sha256(key.encode("utf-8")).hexdigest()

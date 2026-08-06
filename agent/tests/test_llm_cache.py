"""Tests for prompt/response caching and cache backend selection."""

import sys
import types

from app.core.config import settings
from app.llm.cache import (
    MemoryCache,
    RedisCache,
    SqliteCache,
    build_cache,
    hash_request,
)


class _FakeRedisClient:
    def __init__(self) -> None:
        self.data: dict = {}

    def get(self, key: str):
        return self.data.get(key)

    def set(self, key: str, value: str, ex=None) -> None:
        self.data[key] = value

    def delete(self, key: str) -> None:
        self.data.pop(key, None)

    def ping(self) -> bool:
        return True


def _fake_redis_module(client: _FakeRedisClient) -> types.ModuleType:
    module = types.ModuleType("redis")

    class _Redis:
        @classmethod
        def from_url(cls, url: str, **kwargs) -> _FakeRedisClient:
            return client

    module.Redis = _Redis
    return module


def test_memory_cache_roundtrip():
    cache = MemoryCache()
    assert cache.get("k") is None
    cache.set("k", "v")
    assert cache.get("k") == "v"
    cache.delete("k")
    assert cache.get("k") is None


def test_memory_cache_expiry():
    cache = MemoryCache()
    cache.set("k", "v", ttl=-5)
    assert cache.get("k") is None


def test_memory_cache_ping():
    assert MemoryCache().ping() is True


def test_memory_cache_len():
    cache = MemoryCache()
    assert len(cache) == 0
    cache.set("k", "v")
    assert len(cache) == 1


def test_sqlite_cache_roundtrip(tmp_path):
    cache = SqliteCache(str(tmp_path / "c.db"))
    cache.set("k", "v")
    assert cache.get("k") == "v"
    cache.set("k", "v2")
    assert cache.get("k") == "v2"


def test_sqlite_cache_missing_key(tmp_path):
    cache = SqliteCache(str(tmp_path / "c.db"))
    assert cache.get("nope") is None


def test_sqlite_cache_ping(tmp_path):
    cache = SqliteCache(str(tmp_path / "c.db"))
    cache.set("k", "v", ttl=10)
    assert cache.get("k") == "v"
    assert cache.ping() is True
    reopen = SqliteCache(str(tmp_path / "c.db"))
    assert reopen.get("k") == "v"
    cache.set("expired", "x", ttl=-1)
    assert cache.get("expired") is None


def test_sqlite_cache_memory_path():
    cache = SqliteCache(":memory:")
    cache.set("k", "v")
    assert cache.get("k") == "v"


def test_build_cache_backend_memory(monkeypatch):
    monkeypatch.setattr(settings, "agent_llm_cache_backend", "memory")
    assert isinstance(build_cache(settings), MemoryCache)


def test_build_cache_backend_sqlite(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "agent_llm_cache_backend", "sqlite")
    monkeypatch.setattr(settings, "agent_llm_cache_path", str(tmp_path / "llm.db"))
    assert isinstance(build_cache(settings), SqliteCache)


def test_build_cache_redis_without_url_falls_back_to_memory(monkeypatch):
    monkeypatch.setattr(settings, "agent_llm_cache_backend", "redis")
    monkeypatch.setattr(settings, "agent_llm_redis_url", "")
    assert isinstance(build_cache(settings), MemoryCache)


def test_redis_cache_operations(monkeypatch):
    client = _FakeRedisClient()
    monkeypatch.setitem(sys.modules, "redis", _fake_redis_module(client))
    cache = RedisCache("redis://localhost:6379/0")
    assert cache.ping() is True
    cache.set("k", "v", ttl=10)
    assert cache.get("k") == "v"
    cache.set("k", "v2")
    assert cache.get("k") == "v2"
    cache.delete("k")
    assert cache.get("k") is None


def test_build_cache_redis_unavailable_falls_back(monkeypatch):
    client = _FakeRedisClient()
    client.ping = lambda: False  # type: ignore[method-assign]
    monkeypatch.setitem(sys.modules, "redis", _fake_redis_module(client))
    monkeypatch.setattr(settings, "agent_llm_cache_backend", "redis")
    monkeypatch.setattr(settings, "agent_llm_redis_url", "redis://localhost:6379/0")
    assert isinstance(build_cache(settings), MemoryCache)


def test_build_cache_redis_available(monkeypatch):
    client = _FakeRedisClient()
    monkeypatch.setitem(sys.modules, "redis", _fake_redis_module(client))
    monkeypatch.setattr(settings, "agent_llm_cache_backend", "redis")
    monkeypatch.setattr(settings, "agent_llm_redis_url", "redis://localhost:6379/0")
    assert isinstance(build_cache(settings), RedisCache)


def test_hash_request_is_whitespace_insensitive():
    a = hash_request("openai", "gpt-4o-mini", "  system   prompt ", "user  prompt")
    b = hash_request("openai", "gpt-4o-mini", " system prompt ", "user prompt")
    assert a == b


def test_hash_request_differs_across_inputs():
    base = hash_request("openai", "gpt-4o-mini", "system", "user")
    other_models = hash_request("openai", "gpt-4o", "system", "user")
    other_prompts = hash_request("openai", "gpt-4o-mini", "system", "user2")
    other_providers = hash_request("anthropic", "claude", "system", "user")
    assert len({base, other_models, other_prompts, other_providers}) == 4

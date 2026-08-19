"""In-memory sliding-window rate limiting for authentication endpoints.

WIQ-V1-017.

Design notes
------------
- Limits are enforced per process. In a multi-instance deployment every
  instance keeps its own counters, so effective limits scale with the number
  of instances. Use a shared store (e.g. Redis) if strict global limits are
  required; the application currently has no Redis support.
- Client IPs come from the direct connection only; ``X-Forwarded-For`` is
  intentionally not trusted because the application has no proxy-aware IP
  handling (see ``app/core/middleware.py``).
- Timestamps expire after the configured window and are purged lazily, so
  memory stays bounded.
- Limits are read from :mod:`app.core.config` settings on every check, which
  keeps the limiter deterministic and easy to configure in tests.
"""

import threading
import time
from collections import deque
from dataclasses import dataclass

from fastapi import HTTPException, Request, status

from app.core.config import settings

# Scopes that additionally enforce a per-account limit. Only scopes that
# carry an account identifier can use account-level limiting.
ACCOUNT_LIMIT_SCOPES = frozenset({"login"})


def _now() -> float:
    return time.monotonic()


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int


class SlidingWindowRateLimiter:
    """Thread-safe in-memory sliding-window limiter keyed by string identity.

    A key may pass at most ``limit`` checks per rolling ``window_seconds``.
    Expired timestamps are purged lazily; when the key table reaches
    ``max_entries`` the limiter sweeps expired keys and then fails closed.
    """

    def __init__(self, *, max_entries: int = 100_000) -> None:
        self._hits: dict[str, deque[float]] = {}
        self._max_entries = max_entries
        self._lock = threading.Lock()

    def check(
        self,
        key: str,
        *,
        limit: int,
        window_seconds: int,
        now: float | None = None,
    ) -> RateLimitDecision:
        """Record a check for ``key`` and return whether it is allowed.

        ``limit <= 0`` disables the limiter for the key. ``now`` is
        injectable so behaviour is deterministic under test.
        """
        if limit <= 0:
            return RateLimitDecision(allowed=True, retry_after_seconds=0)

        now = _now() if now is None else now

        with self._lock:
            cutoff = now - window_seconds

            timestamps = self._hits.get(key)
            if timestamps is not None:
                while timestamps and timestamps[0] <= cutoff:
                    timestamps.popleft()
                if not timestamps:
                    del self._hits[key]
                    timestamps = None

            if timestamps is None:
                if len(self._hits) >= self._max_entries:
                    self._purge_all(now, window_seconds)
                    if len(self._hits) >= self._max_entries:
                        # At capacity: fail closed rather than grow unbounded.
                        return RateLimitDecision(allowed=False, retry_after_seconds=window_seconds)
                timestamps = deque()
                self._hits[key] = timestamps

            if len(timestamps) >= limit:
                oldest = timestamps[0]
                retry_after = max(1, int(window_seconds - (now - oldest)) + 1)
                return RateLimitDecision(allowed=False, retry_after_seconds=retry_after)

            timestamps.append(now)
            return RateLimitDecision(allowed=True, retry_after_seconds=0)

    def _purge_all(self, now: float, window_seconds: int) -> None:
        cutoff = now - window_seconds
        for key, timestamps in list(self._hits.items()):
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()
            if not timestamps:
                del self._hits[key]

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()

    def clear_key(self, key: str) -> None:
        with self._lock:
            self._hits.pop(key, None)

    def __len__(self) -> int:
        with self._lock:
            return len(self._hits)


rate_limiter = SlidingWindowRateLimiter()


def get_client_ip(request: Request) -> str:
    """Client IP from the direct connection only.

    ``X-Forwarded-For`` is not trusted: the application has no proxy-aware
    IP handling (see ``app/core/middleware.py``).
    """
    client = request.client
    return client.host if client is not None else "unknown"


def check_rate_limit(
    request: Request,
    scope: str,
    *,
    account_identifier: str | None = None,
) -> None:
    """Enforce per-IP and (where applicable) per-account limits for ``scope``.

    Raises HTTP 429 with a ``Retry-After`` header when a limit is exceeded.
    The response body follows the application's standard error format and
    reveals nothing about whether an account exists.
    """
    window_seconds = settings.rate_limit_window_seconds

    decisions = [
        rate_limiter.check(
            f"{scope}:ip:{get_client_ip(request)}",
            limit=getattr(settings, f"{scope}_rate_limit_max"),
            window_seconds=window_seconds,
        )
    ]

    if account_identifier is not None and scope in ACCOUNT_LIMIT_SCOPES:
        decisions.append(
            rate_limiter.check(
                f"{scope}:account:{account_identifier}",
                limit=getattr(settings, f"{scope}_account_rate_limit_max"),
                window_seconds=window_seconds,
            )
        )

    if all(decision.allowed for decision in decisions):
        return

    retry_after = max(decision.retry_after_seconds for decision in decisions)
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Too many requests. Please try again later.",
        headers={"Retry-After": str(retry_after)},
    )

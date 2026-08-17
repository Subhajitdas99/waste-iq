import threading
from typing import Callable

from app.coordinator.event_handler import EventEnvelope

Processor = Callable[[EventEnvelope], None]


class InProcessTaskQueue:
    """Minimal in-process queue for event delivery.

    Swapped for an external queue (e.g. Redis/arq or a LangGraph executor) in a
    later phase; the interface is intentionally small so callers do not change.
    """

    def __init__(self) -> None:
        self._pending: list[EventEnvelope] = []
        self._lock = threading.Lock()
        self._enqueued = 0

    def enqueue(self, envelope: EventEnvelope) -> int:
        with self._lock:
            self._pending.append(envelope)
            self._enqueued += 1
        return self._enqueued

    def drain(self, processor: Processor) -> tuple[int, int]:
        with self._lock:
            batch, self._pending = self._pending, []
        succeeded = 0
        for envelope in batch:
            try:
                processor(envelope)
                succeeded += 1
            except Exception:  # noqa: BLE001 - failures are counted, not fatal
                continue
        return succeeded, len(batch)

    def size(self) -> int:
        with self._lock:
            return len(self._pending)

    @property
    def enqueued_count(self) -> int:
        return self._enqueued

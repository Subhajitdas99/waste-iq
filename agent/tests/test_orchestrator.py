from datetime import datetime, timezone

from app.coordinator.event_handler import EventEnvelope, parse_event
from app.coordinator.orchestrator import EventOrchestrator
from app.coordinator.task_queue import InProcessTaskQueue
from app.db.models import AgentRun
from app.db.session import SessionLocal


def _envelope(
    delivery_id: str = "evt-1", event_type: str = "issues", action: str | None = "opened"
) -> EventEnvelope:
    return EventEnvelope(
        delivery_id=delivery_id,
        event_type=event_type,
        event_action=action,
        payload={},
        received_at=datetime.now(timezone.utc),
    )


def test_process_records_run_once():
    envelope = _envelope()
    db = SessionLocal()
    try:
        first = EventOrchestrator(db).process(envelope)
        second = EventOrchestrator(db).process(envelope)
        count = db.query(AgentRun).filter(AgentRun.delivery_id == "evt-1").count()
    finally:
        db.close()

    assert first.id == second.id
    assert count == 1
    assert first.status == "processed"


def test_parse_event_returns_none_for_missing_headers():
    assert parse_event({}, {}) is None
    assert parse_event({}, {"x-github-delivery": "d", "x-github-event": "issues"}) is not None


def test_parse_event_captures_action():
    headers = {"x-github-delivery": "d", "x-github-event": "pull_request"}
    envelope = parse_event({"action": "opened"}, headers)
    assert envelope is not None
    assert envelope.event_action == "opened"


def test_parse_event_rejects_non_dict_payload():
    assert parse_event([1, 2], {"x-github-delivery": "d", "x-github-event": "issues"}) is None


def test_task_queue_drains_all():
    queue = InProcessTaskQueue()
    queue.enqueue(_envelope(delivery_id="q-1"))
    queue.enqueue(_envelope(delivery_id="q-2"))
    assert queue.size() == 2

    processed = []
    succeeded, total = queue.drain(lambda e: processed.append(e))

    assert succeeded == 2
    assert total == 2
    assert queue.size() == 0
    assert queue.enqueued_count == 2


def test_task_queue_counts_failures():
    queue = InProcessTaskQueue()
    queue.enqueue(_envelope(delivery_id="q-3"))

    def boom(_: EventEnvelope) -> None:
        raise RuntimeError("handler failure")

    succeeded, total = queue.drain(boom)

    assert succeeded == 0
    assert total == 1

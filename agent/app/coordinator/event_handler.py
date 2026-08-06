from datetime import datetime, timezone

from pydantic import BaseModel


class EventEnvelope(BaseModel):
    delivery_id: str
    event_type: str
    event_action: str | None = None
    payload: dict
    received_at: datetime


def parse_event(payload: dict, headers: dict) -> EventEnvelope | None:
    """Normalize a raw GitHub webhook into a typed envelope.

    Returns None for malformed or unrecognized events.
    """
    delivery_id = headers.get("x-github-delivery")
    event_type = headers.get("x-github-event")
    if not delivery_id or not event_type or not isinstance(payload, dict):
        return None
    action = payload.get("action")
    return EventEnvelope(
        delivery_id=delivery_id,
        event_type=event_type,
        event_action=str(action) if action else None,
        payload=payload,
        received_at=datetime.now(timezone.utc),
    )

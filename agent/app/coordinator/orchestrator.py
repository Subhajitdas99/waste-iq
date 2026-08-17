import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.coordinator.event_handler import EventEnvelope
from app.db.models import AgentRun

logger = logging.getLogger(__name__)


class EventOrchestrator:
    """Phase 0 dispatcher: records every delivery idempotently in the state DB.

    Assistant handlers are wired into `HANDLERS` in later slices; Phase 0 only
    records runs (no assistant logic yet).
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def process(self, envelope: EventEnvelope) -> AgentRun:
        existing = (
            self.db.query(AgentRun).filter(AgentRun.delivery_id == envelope.delivery_id).first()
        )
        if existing:
            logger.info("duplicate delivery ignored delivery=%s", envelope.delivery_id)
            return existing

        run = AgentRun(
            delivery_id=envelope.delivery_id,
            event_type=envelope.event_type,
            event_action=envelope.event_action,
            status="processed",
        )
        self.db.add(run)
        try:
            self.db.commit()
        except IntegrityError:
            # Lost the race to another worker processing the same delivery.
            self.db.rollback()
            return (
                self.db.query(AgentRun).filter(AgentRun.delivery_id == envelope.delivery_id).one()
            )
        self.db.refresh(run)
        logger.info(
            "processed event delivery=%s type=%s action=%s",
            envelope.delivery_id,
            envelope.event_type,
            envelope.event_action,
        )
        return run

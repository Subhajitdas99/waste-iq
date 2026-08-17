from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import AgentRun
from app.db.session import get_db

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _require_auth(authorization: str | None) -> None:
    expected = settings.agent_admin_api_token
    if not expected or authorization != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="unauthorized")


@router.get("/runs")
async def list_runs(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
    limit: int = 50,
) -> dict:
    _require_auth(authorization)
    rows = db.query(AgentRun).order_by(AgentRun.id.desc()).limit(limit).all()
    return {
        "runs": [
            {
                "id": run.id,
                "delivery_id": run.delivery_id,
                "event_type": run.event_type,
                "event_action": run.event_action,
                "assistant": run.assistant,
                "status": run.status,
                "outcome": run.outcome,
                "created_at": run.created_at.isoformat(),
            }
            for run in rows
        ]
    }

from fastapi import APIRouter, Depends

from app.core.dependencies import require_roles
from app.models.user import User
from app.services.jobs import last_runs

router = APIRouter(
    prefix="/admin/jobs",
    tags=["Admin Jobs"],
)


@router.get("/status")
def job_status(
    current_user: User = Depends(require_roles("admin")),
) -> dict[str, str | None]:
    return {
        "reservation_sweep": (
            last_runs["reservation_sweep"].isoformat() if last_runs["reservation_sweep"] else None
        ),
        "aging_pickups": (
            last_runs["aging_pickups"].isoformat() if last_runs["aging_pickups"] else None
        ),
    }

from fastapi import APIRouter

from app.services.jobs import last_runs

router = APIRouter(
    prefix="/admin/jobs",
    tags=["Admin Jobs"],
)


@router.get("/status")
def job_status():
    return {
        "reservation_sweep": (
            last_runs["reservation_sweep"].isoformat()
            if last_runs["reservation_sweep"]
            else None
        ),
        "aging_pickups": (
            last_runs["aging_pickups"].isoformat()
            if last_runs["aging_pickups"]
            else None
        ),
    }
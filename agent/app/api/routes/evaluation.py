"""Evaluation status endpoint — last benchmark run summary."""

from fastapi import APIRouter

from app.core.config import settings
from app.evaluation.report import load_state

router = APIRouter(tags=["evaluation"])


@router.get("/api/evaluation/status")
def evaluation_status() -> dict:
    """Return the last benchmark run summary (or empty placeholders)."""
    state = load_state(settings.agent_evaluation_state_path)
    if state is None:
        return {
            "benchmark_version": settings.agent_benchmark_version,
            "last_run": None,
            "run_id": None,
            "overall_score": None,
            "failures": None,
            "cases_executed": None,
            "hallucinations": None,
            "weakest_category": None,
            "strongest_category": None,
            "gates": None,
        }
    return state

"""PR Review Agent (Phase 2).

Read-only pull request analyzer layered on the Phase 1 Repository Context
Service. Produces evidence-backed review objects; never merges, approves,
edits code, or comments on GitHub.
"""

from app.review.review_agent import ReviewAgent  # noqa: F401
from app.review.review_engine import ReviewEngine  # noqa: F401
from app.review.review_models import (  # noqa: F401
    PRReview,
    ReviewFinding,
    ReviewRequest,
    ReviewStatus,
    ReviewUnavailable,
)
from app.review.review_service import ReviewService  # noqa: F401

__version__ = "2.0.0"

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_roles
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsInsight,
    AnalyticsOverview,
    CarbonSavings,
    CollectorPerformance,
    DealerPerformance,
    MaterialBreakdown,
    MonthlyStat,
)
from app.services.analytics import (
    generate_insights,
    get_carbon_savings,
    get_collector_performance,
    get_dealer_performance,
    get_material_breakdown,
    get_monthly_analytics,
    get_overview_analytics,
)

router = APIRouter()


@router.get("/overview", response_model=AnalyticsOverview)
def analytics_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> AnalyticsOverview:
    return get_overview_analytics(db)


@router.get("/materials", response_model=MaterialBreakdown)
def analytics_materials(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> MaterialBreakdown:
    return get_material_breakdown(db)


@router.get("/monthly", response_model=list[MonthlyStat])
def analytics_monthly(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> list[MonthlyStat]:
    return get_monthly_analytics(db)


@router.get("/collectors", response_model=list[CollectorPerformance])
def analytics_collectors(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> list[CollectorPerformance]:
    return get_collector_performance(db)


@router.get("/dealers", response_model=list[DealerPerformance])
def analytics_dealers(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> list[DealerPerformance]:
    return get_dealer_performance(db)


@router.get("/carbon", response_model=CarbonSavings)
def analytics_carbon(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> CarbonSavings:
    return get_carbon_savings(db)


@router.get("/insights", response_model=list[AnalyticsInsight])
def analytics_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> list[AnalyticsInsight]:
    return generate_insights(db)

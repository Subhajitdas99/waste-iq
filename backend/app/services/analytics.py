"""Analytics business logic: SQL aggregations and deterministic, rule-based insights."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from statistics import median

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.collector_assignment import CollectorAssignment
from app.models.dealer_profile import DealerApprovalStatus, DealerProfile
from app.models.inventory_lot import InventoryLot, InventoryLotStatus
from app.models.pickup_dispute import DisputeResolution, PickupDispute
from app.models.pickup_request import PickupRequest, PickupStatus
from app.models.user import User, UserRole
from app.schemas.analytics import (
    AnalyticsInsight,
    AnalyticsOverview,
    CarbonSavings,
    CollectorPerformance,
    DealerPerformance,
    MaterialBreakdown,
    MonthlyStat,
    PilotActivity,
    PilotCollectionKpis,
    PilotMetrics,
    PilotReliability,
    PilotTiming,
    PilotWeightQuality,
    PilotWindow,
)
from app.services.stats import count_pickups, count_users, sum_collected_weight

# ~0.42 kg CO2e saved per kg of waste recycled (matches frontend recycling model).
CO2_SAVED_PER_KG = 0.42
# Rough yearly CO2 absorption of a single mature tree, in kg.
CO2_ABSORBED_PER_TREE_KG = 21.0
MONTHS_TO_REPORT = 12

_MATERIAL_BUCKET_KEYWORDS: dict[str, tuple[str, ...]] = {
    "plastic": ("plastic", "pet", "hdpe", "ldpe", "polythene", "polyethylene", "pvc"),
    "paper": ("paper", "cardboard", "carton", "newspaper", "newsprint"),
    "metal": ("metal", "aluminium", "aluminum", "steel", "iron", "tin", "copper", "brass"),
    "glass": ("glass", "ceramic"),
    "e_waste": ("e-waste", "e_waste", "ewaste", "electronic", "electronics", "electrical"),
    "organic": ("organic", "food", "kitchen", "garden", "biodegradable"),
}

_MATERIAL_LABELS: dict[str, str] = {
    "plastic": "Plastic",
    "paper": "Paper",
    "metal": "Metal",
    "glass": "Glass",
    "e_waste": "E-Waste",
    "organic": "Organic",
    "other": "Other",
}

# ─── Small helpers ───────────────────────────────────────────────────────────


def _utc_naive(value: datetime) -> datetime:
    """Normalize any datetime to a naive UTC datetime for portable arithmetic."""
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def _month_key(value: datetime) -> str:
    return _utc_naive(value).strftime("%Y-%m")


def _material_bucket(text: str | None) -> str:
    if not text:
        return "other"
    normalized = text.strip().lower()
    for bucket, keywords in _MATERIAL_BUCKET_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return bucket
    return "other"


def _categorize(category: str | None, waste_type: str | None) -> str:
    bucket = _material_bucket(category)
    if bucket != "other":
        return bucket
    return _material_bucket(waste_type)


@dataclass
class _MaterialStats:
    count: int = 0
    weight: float = 0.0


def _fetch_material_stats(db: Session) -> dict[str, _MaterialStats]:
    """Aggregate completed pickups by material bucket: counts and collected weight."""
    rows = db.execute(
        select(
            PickupRequest.category,
            PickupRequest.waste_type,
            func.count(PickupRequest.id),
            func.coalesce(func.sum(CollectorAssignment.weight_kg), 0.0),
        )
        .outerjoin(CollectorAssignment, CollectorAssignment.request_id == PickupRequest.id)
        .where(PickupRequest.status == PickupStatus.completed)
        .group_by(PickupRequest.category, PickupRequest.waste_type)
    ).all()

    buckets = {bucket: _MaterialStats() for bucket in _MATERIAL_LABELS}
    for row in rows:
        bucket = _categorize(row[0], row[1])
        buckets[bucket].count += int(row[2])
        buckets[bucket].weight += float(row[3])
    return buckets


# ─── Overview ────────────────────────────────────────────────────────────────


def get_overview_analytics(db: Session) -> AnalyticsOverview:
    total_pickups = count_pickups(db)
    completed_pickups = count_pickups(db, PickupStatus.completed)
    pending_pickups = count_pickups(db, PickupStatus.pending)
    cancelled_pickups = count_pickups(db, PickupStatus.cancelled)
    total_weight_kg = sum_collected_weight(db)

    completed_rate = round(completed_pickups / total_pickups * 100, 2) if total_pickups else 0.0

    return AnalyticsOverview(
        total_users=count_users(db),
        citizens=count_users(db, UserRole.citizen),
        collectors=count_users(db, UserRole.collector),
        dealers=count_users(db, UserRole.dealer),
        total_pickups=total_pickups,
        completed_pickups=completed_pickups,
        pending_pickups=pending_pickups,
        cancelled_pickups=cancelled_pickups,
        total_weight_kg=round(float(total_weight_kg), 2),
        completed_rate=completed_rate,
    )


# ─── Materials ───────────────────────────────────────────────────────────────


def get_material_breakdown(db: Session) -> MaterialBreakdown:
    stats = _fetch_material_stats(db)
    return MaterialBreakdown(
        plastic=stats["plastic"].count,
        paper=stats["paper"].count,
        metal=stats["metal"].count,
        glass=stats["glass"].count,
        e_waste=stats["e_waste"].count,
        organic=stats["organic"].count,
        other=stats["other"].count,
    )


# ─── Monthly trend ───────────────────────────────────────────────────────────


def _last_n_month_keys(now: datetime, count: int) -> list[str]:
    anchor = now.year * 12 + (now.month - 1)
    return [
        f"{(anchor - offset) // 12:04d}-{(anchor - offset) % 12 + 1:02d}"
        for offset in range(count - 1, -1, -1)
    ]


def get_monthly_analytics(db: Session) -> list[MonthlyStat]:
    """Monthly pickup statistics for the last 12 months, oldest first.

    Every month in the window is included, zero-filled when there is no activity.
    """
    now = datetime.now(timezone.utc)
    keys = _last_n_month_keys(now, MONTHS_TO_REPORT)
    by_month: dict[str, dict[str, float | int]] = {
        key: {"pickup_count": 0, "completed": 0, "weight": 0.0} for key in keys
    }

    start = datetime.strptime(f"{keys[0]}-01", "%Y-%m-%d")
    rows = db.execute(
        select(
            PickupRequest.created_at,
            PickupRequest.status,
            func.coalesce(CollectorAssignment.weight_kg, 0.0),
        )
        .outerjoin(CollectorAssignment, CollectorAssignment.request_id == PickupRequest.id)
        .where(PickupRequest.created_at >= start)
    ).all()

    for row in rows:
        key = _month_key(row[0])
        if key not in by_month:
            continue
        stats = by_month[key]
        stats["pickup_count"] = int(stats["pickup_count"]) + 1
        if row[1] == PickupStatus.completed:
            stats["completed"] = int(stats["completed"]) + 1
        stats["weight"] = float(stats["weight"]) + float(row[2])

    return [
        MonthlyStat(
            month=key,
            pickup_count=int(stats["pickup_count"]),
            completed=int(stats["completed"]),
            weight=round(float(stats["weight"]), 2),
        )
        for key, stats in by_month.items()
    ]


# ─── Collector performance ───────────────────────────────────────────────────


@dataclass
class _CollectorAggregate:
    name: str
    total: int = 0
    completed: int = 0
    response_seconds: float = 0.0


def get_collector_performance(db: Session) -> list[CollectorPerformance]:
    rows = db.execute(
        select(
            User.id,
            User.name,
            PickupRequest.created_at,
            PickupRequest.status,
            CollectorAssignment.accepted_at,
        )
        .join(CollectorAssignment, CollectorAssignment.collector_id == User.id)
        .join(PickupRequest, PickupRequest.id == CollectorAssignment.request_id)
        .order_by(User.id, PickupRequest.created_at)
    ).all()

    aggregates: dict[int, _CollectorAggregate] = {}
    for row in rows:
        aggregate = aggregates.get(row[0])
        if aggregate is None:
            aggregate = aggregates[row[0]] = _CollectorAggregate(name=row[1])
        aggregate.total += 1
        if row[3] == PickupStatus.completed:
            aggregate.completed += 1
            if row[4] is not None:
                elapsed = (_utc_naive(row[4]) - _utc_naive(row[2])).total_seconds()
                aggregate.response_seconds += max(elapsed, 0.0)

    performances = [
        CollectorPerformance(
            collector_id=collector_id,
            collector_name=aggregate.name,
            completed_jobs=aggregate.completed,
            completion_rate=(
                round(aggregate.completed / aggregate.total * 100, 2) if aggregate.total else 0.0
            ),
            average_response_time=(
                round(aggregate.response_seconds / 3600 / aggregate.completed, 2)
                if aggregate.completed
                else 0.0
            ),
        )
        for collector_id, aggregate in aggregates.items()
    ]
    performances.sort(key=lambda p: (-p.completed_jobs, -p.completion_rate, p.collector_name))
    return performances


# ─── Dealer performance ──────────────────────────────────────────────────────


def get_dealer_performance(db: Session) -> list[DealerPerformance]:
    rows = db.execute(
        select(
            InventoryLot.reserved_by_dealer_id,
            func.count(InventoryLot.id),
            func.coalesce(func.sum(InventoryLot.weight_kg), 0.0),
        )
        .where(
            InventoryLot.status == InventoryLotStatus.sold,
            InventoryLot.reserved_by_dealer_id.is_not(None),
        )
        .group_by(InventoryLot.reserved_by_dealer_id)
    ).all()

    if not rows:
        return []

    dealer_names: dict[int, str] = {}
    for profile in db.scalars(select(DealerProfile)).all():
        dealer_names[profile.user_id] = profile.business_name
    for user in db.scalars(select(User).where(User.role == UserRole.dealer)).all():
        dealer_names.setdefault(user.id, user.name)

    performances = [
        DealerPerformance(
            dealer_id=row[0],
            dealer_name=dealer_names.get(row[0], "Unknown dealer"),
            materials_processed=int(row[1]),
            total_weight=round(float(row[2]), 2),
        )
        for row in rows
    ]
    performances.sort(key=lambda p: (-p.total_weight, -p.materials_processed, p.dealer_name))
    return performances


# ─── Carbon savings ──────────────────────────────────────────────────────────


def get_carbon_savings(db: Session) -> CarbonSavings:
    stats = _fetch_material_stats(db)
    total_weight = sum(stat.weight for stat in stats.values())
    co2_saved = round(total_weight * CO2_SAVED_PER_KG, 2)

    return CarbonSavings(
        estimated_co2_saved=co2_saved,
        trees_equivalent=round(co2_saved / CO2_ABSORBED_PER_TREE_KG, 1),
        plastic_recycled=round(stats["plastic"].weight, 2),
        paper_recycled=round(stats["paper"].weight, 2),
    )


# ─── Rule-based AI insights ──────────────────────────────────────────────────


def generate_insights(db: Session) -> list[AnalyticsInsight]:
    """Deterministic, rule-based insights computed from the live analytics."""
    insights: list[AnalyticsInsight] = []

    breakdown = get_material_breakdown(db)
    material_counts = [
        (bucket, getattr(breakdown, bucket))
        for bucket in ("plastic", "paper", "metal", "glass", "e_waste", "organic", "other")
    ]
    most_recycled = max(material_counts, key=lambda item: item[1])
    if most_recycled[1] > 0:
        insights.append(
            AnalyticsInsight(
                key="most_recycled_material",
                title="Most Recycled Material",
                message=(
                    f"{_MATERIAL_LABELS[most_recycled[0]]} is the most recycled material with "
                    f"{most_recycled[1]} completed pickup(s)."
                ),
            )
        )

    collectors = get_collector_performance(db)
    if collectors:
        top_collector = collectors[0]
        insights.append(
            AnalyticsInsight(
                key="top_collector",
                title="Highest Performing Collector",
                message=(
                    f"{top_collector.collector_name} leads collectors with "
                    f"{top_collector.completed_jobs} completed job(s) and a "
                    f"{top_collector.completion_rate}% completion rate."
                ),
            )
        )

    dealers = get_dealer_performance(db)
    if dealers:
        top_dealer = dealers[0]
        insights.append(
            AnalyticsInsight(
                key="top_dealer",
                title="Highest Performing Dealer",
                message=(
                    f"{top_dealer.dealer_name} processed the most material with "
                    f"{top_dealer.total_weight} kg across {top_dealer.materials_processed} lot(s)."
                ),
            )
        )

    carbon = get_carbon_savings(db)
    if carbon.estimated_co2_saved > 0:
        insights.append(
            AnalyticsInsight(
                key="carbon_savings",
                title="Estimated Carbon Savings",
                message=(
                    f"The platform has saved an estimated {carbon.estimated_co2_saved} kg of CO2, "
                    f"equivalent to {carbon.trees_equivalent} tree(s)."
                ),
            )
        )

    monthly = get_monthly_analytics(db)
    recent_completed = sum(entry.completed for entry in monthly[MONTHS_TO_REPORT // 2 :])
    previous_completed = sum(entry.completed for entry in monthly[: MONTHS_TO_REPORT // 2])
    if previous_completed > 0:
        change = round((recent_completed - previous_completed) / previous_completed * 100, 1)
        if change >= 5:
            message = (
                f"Completed pickups are up {change}% in the last 6 months compared to "
                "the previous 6 months."
            )
        elif change <= -5:
            message = (
                f"Completed pickups are down {abs(change)}% in the last 6 months compared to "
                "the previous 6 months."
            )
        else:
            message = "Completed pickups have remained steady over the last 12 months."
        insights.append(
            AnalyticsInsight(
                key="pickup_trend",
                title="Pickup Completion Trend",
                message=message,
            )
        )

    return insights


# ─── Pilot metrics (WIQ-V1-052) ───────────────────────────────────────────────

PILOT_WINDOW_DAYS = 30


def _median_or_none(values: list[float]) -> float | None:
    return round(float(median(values)), 2) if values else None


def _mean_or_none(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 2) if values else None


def _isoformat_or_none(value: datetime | None) -> str | None:
    if value is None:
        return None
    normalized = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return normalized.isoformat()


def _resolve_pilot_window(
    db: Session,
) -> tuple[datetime, datetime, int]:
    """Return (start, end, days) for the pilot reporting window.

    Uses the earliest pickup request as the start so the window reflects the
    actual pilot history (never empty). The end is "now" (UTC). Falls back to
    the configured default length when no requests exist yet.
    """
    end = datetime.now(timezone.utc)
    earliest = db.scalar(select(func.min(PickupRequest.created_at)))
    if earliest is None:
        start = end - timedelta(days=PILOT_WINDOW_DAYS)
        return start, end, PILOT_WINDOW_DAYS

    if earliest.tzinfo is None:
        earliest = earliest.replace(tzinfo=timezone.utc)
    days = max((end - earliest).days, 1)
    return earliest, end, days


def _get_pilot_collection_kpis(db: Session) -> PilotCollectionKpis:
    total = count_pickups(db)
    completed = count_pickups(db, PickupStatus.completed)
    cancelled = count_pickups(db, PickupStatus.cancelled)
    total_weight = float(sum_collected_weight(db))
    completion_rate = round(completed / total * 100, 2) if total else 0.0
    average_weight = round(total_weight / completed, 2) if completed else 0.0

    active_citizens = int(
        db.scalar(
            select(func.count(func.distinct(PickupRequest.user_id))).where(
                PickupRequest.user_id.is_not(None)
            )
        )
        or 0
    )
    active_collectors = int(
        db.scalar(
            select(func.count(func.distinct(CollectorAssignment.collector_id))).where(
                CollectorAssignment.collector_id.is_not(None)
            )
        )
        or 0
    )

    return PilotCollectionKpis(
        total_pickups=total,
        completed_pickups=completed,
        cancelled_pickups=cancelled,
        completion_rate=completion_rate,
        total_weight_kg=round(total_weight, 2),
        average_weight_kg=average_weight,
        active_citizens=active_citizens,
        active_collectors=active_collectors,
    )


def _get_pilot_timing(db: Session) -> PilotTiming:
    rows = db.execute(
        select(
            PickupRequest.created_at,
            CollectorAssignment.accepted_at,
            CollectorAssignment.completed_at,
            PickupRequest.status,
        ).join(CollectorAssignment, CollectorAssignment.request_id == PickupRequest.id)
    ).all()

    request_to_accept: list[float] = []
    accept_to_complete: list[float] = []
    request_to_complete: list[float] = []

    for created_at, accepted_at, completed_at, status in rows:
        if created_at is None or accepted_at is None:
            continue
        accept_delta = (_utc_naive(accepted_at) - _utc_naive(created_at)).total_seconds()
        if accept_delta < 0:
            continue
        request_to_accept.append(accept_delta / 3600)

        if status == PickupStatus.completed and completed_at is not None:
            completion_delta = (_utc_naive(completed_at) - _utc_naive(created_at)).total_seconds()
            if completion_delta >= 0:
                request_to_complete.append(completion_delta / 3600)

            collection_delta = (_utc_naive(completed_at) - _utc_naive(accepted_at)).total_seconds()
            if collection_delta >= 0:
                accept_to_complete.append(collection_delta / 3600)

    return PilotTiming(
        median_request_to_acceptance_hours=_median_or_none(request_to_accept),
        median_acceptance_to_completion_hours=_median_or_none(accept_to_complete),
        median_request_to_completion_hours=_median_or_none(request_to_complete),
        average_request_to_acceptance_hours=_mean_or_none(request_to_accept),
        average_acceptance_to_completion_hours=_mean_or_none(accept_to_complete),
        sample_size=len(request_to_accept),
    )


def _get_pilot_weight_quality(db: Session) -> PilotWeightQuality:
    rows = db.execute(
        select(
            PickupRequest.estimated_weight_kg,
            CollectorAssignment.weight_kg,
            PickupRequest.id,
        )
        .outerjoin(CollectorAssignment, CollectorAssignment.request_id == PickupRequest.id)
        .where(PickupRequest.status == PickupStatus.completed)
    ).all()

    pickups_with_estimate = 0
    pickups_with_recorded_weight = 0
    ratios: list[float] = []
    deltas: list[float] = []
    for estimate, recorded, _ in rows:
        if estimate is not None and estimate > 0:
            pickups_with_estimate += 1
        if recorded is not None and recorded > 0:
            pickups_with_recorded_weight += 1
        if estimate is not None and recorded is not None and estimate > 0 and recorded > 0:
            ratios.append(recorded / estimate)
            deltas.append(abs(recorded - estimate))

    dispute_count = int(db.scalar(select(func.count(PickupDispute.id))) or 0)
    upheld = int(
        db.scalar(
            select(func.count(PickupDispute.id)).where(
                PickupDispute.resolution == DisputeResolution.upheld
            )
        )
        or 0
    )
    corrected = int(
        db.scalar(
            select(func.count(PickupDispute.id)).where(
                PickupDispute.resolution == DisputeResolution.corrected
            )
        )
        or 0
    )

    return PilotWeightQuality(
        pickups_with_estimate=pickups_with_estimate,
        pickups_with_recorded_weight=pickups_with_recorded_weight,
        estimate_vs_actual_ratio=(round(sum(ratios) / len(ratios), 2) if ratios else None),
        median_absolute_estimate_delta_kg=_median_or_none(deltas),
        disputed_pickups=dispute_count,
        disputes_upheld=upheld,
        disputes_corrected=corrected,
    )


def _get_pilot_activity(db: Session, now: datetime) -> PilotActivity:
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)

    pickups_last_7 = int(
        db.scalar(
            select(func.count(PickupRequest.id)).where(PickupRequest.created_at >= seven_days_ago)
        )
        or 0
    )
    pickups_last_30 = int(
        db.scalar(
            select(func.count(PickupRequest.id)).where(PickupRequest.created_at >= thirty_days_ago)
        )
        or 0
    )
    completed_last_7 = int(
        db.scalar(
            select(func.count(PickupRequest.id)).where(
                PickupRequest.created_at >= seven_days_ago,
                PickupRequest.status == PickupStatus.completed,
            )
        )
        or 0
    )
    completed_last_30 = int(
        db.scalar(
            select(func.count(PickupRequest.id)).where(
                PickupRequest.created_at >= thirty_days_ago,
                PickupRequest.status == PickupStatus.completed,
            )
        )
        or 0
    )
    lots_listed = int(
        db.scalar(
            select(func.count(InventoryLot.id)).where(
                InventoryLot.status.in_([InventoryLotStatus.available, InventoryLotStatus.reserved])
            )
        )
        or 0
    )
    lots_sold = int(
        db.scalar(
            select(func.count(InventoryLot.id)).where(
                InventoryLot.status == InventoryLotStatus.sold
            )
        )
        or 0
    )
    pending_dealers = int(
        db.scalar(
            select(func.count(DealerProfile.id)).where(
                DealerProfile.approval_status == DealerApprovalStatus.submitted
            )
        )
        or 0
    )

    return PilotActivity(
        pickups_last_7_days=pickups_last_7,
        pickups_last_30_days=pickups_last_30,
        completed_last_7_days=completed_last_7,
        completed_last_30_days=completed_last_30,
        lots_listed=lots_listed,
        lots_sold=lots_sold,
        pending_dealer_applications=pending_dealers,
    )


def _get_pilot_reliability(db: Session) -> PilotReliability:
    """Compute reliability signals we can derive from authoritative state.

    The audit log captures administrative actions, not API request/response
    outcomes, so it cannot be used to compute an API error rate. Notification
    records are written synchronously and have no failure status, and
    background jobs only record their last successful run. Uptime cannot be
    derived from the database. For each of these we set ``available=False``
    and return ``None`` plus a note so the UI can render "N/A" rather than
    misleading zeros. See docs/WIQ_V1_052_PILOT_METRICS.md.
    """

    return PilotReliability(
        api_error_rate=None,
        api_error_rate_available=False,
        api_error_rate_note=(
            "API request outcomes are not captured in the audit log; "
            "tracking requires middleware-based instrumentation."
        ),
        notification_failure_rate=None,
        notification_failure_rate_available=False,
        notification_failure_rate_note=(
            "Notifications are created synchronously and have no failure "
            "status; failure tracking requires a delivery pipeline."
        ),
        background_job_failures=None,
        background_job_failures_available=False,
        background_job_failures_note=(
            "Background jobs only persist their last successful run; "
            "failure counts require a dedicated job history table."
        ),
        background_job_last_runs={
            "reservation_sweep": _isoformat_or_none(None),
            "aging_pickups": _isoformat_or_none(None),
        },
        platform_uptime_seconds=None,
        platform_uptime_available=False,
        platform_uptime_note=(
            "Platform uptime is not tracked; this metric requires an external "
            "monitoring service."
        ),
    )


def get_pilot_metrics(db: Session) -> PilotMetrics:
    start, end, days = _resolve_pilot_window(db)
    return PilotMetrics(
        window=PilotWindow(
            start=_isoformat_or_none(start),
            end=_isoformat_or_none(end),
            days=days,
        ),
        collection=_get_pilot_collection_kpis(db),
        timing=_get_pilot_timing(db),
        weight_quality=_get_pilot_weight_quality(db),
        activity=_get_pilot_activity(db, end),
        reliability=_get_pilot_reliability(db),
    )

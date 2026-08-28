from pydantic import BaseModel


class AnalyticsOverview(BaseModel):
    total_users: int
    citizens: int
    collectors: int
    dealers: int
    total_pickups: int
    completed_pickups: int
    pending_pickups: int
    cancelled_pickups: int
    total_weight_kg: float
    completed_rate: float


class MaterialBreakdown(BaseModel):
    plastic: int
    paper: int
    metal: int
    glass: int
    e_waste: int
    organic: int
    other: int


class MonthlyStat(BaseModel):
    month: str
    pickup_count: int
    completed: int
    weight: float


class CollectorPerformance(BaseModel):
    collector_id: int
    collector_name: str
    completed_jobs: int
    completion_rate: float
    average_response_time: float


class DealerPerformance(BaseModel):
    dealer_id: int
    dealer_name: str
    materials_processed: int
    total_weight: float


class CarbonSavings(BaseModel):
    estimated_co2_saved: float
    trees_equivalent: float
    plastic_recycled: float
    paper_recycled: float


class AnalyticsInsight(BaseModel):
    key: str
    title: str
    message: str


class PilotCollectionKpis(BaseModel):
    """Headline KPIs for collection operations during the pilot window."""

    total_pickups: int
    completed_pickups: int
    cancelled_pickups: int
    completion_rate: float
    total_weight_kg: float
    average_weight_kg: float
    active_citizens: int
    active_collectors: int


class PilotTiming(BaseModel):
    """Workflow timing metrics derived from request/assignment timestamps."""

    median_request_to_acceptance_hours: float | None
    median_acceptance_to_completion_hours: float | None
    median_request_to_completion_hours: float | None
    average_request_to_acceptance_hours: float | None
    average_acceptance_to_completion_hours: float | None
    sample_size: int


class PilotWeightQuality(BaseModel):
    """Weight estimation accuracy and dispute signal."""

    pickups_with_estimate: int
    pickups_with_recorded_weight: int
    estimate_vs_actual_ratio: float | None
    median_absolute_estimate_delta_kg: float | None
    disputed_pickups: int
    disputes_upheld: int
    disputes_corrected: int


class PilotActivity(BaseModel):
    """Recent pilot activity and marketplace movement."""

    pickups_last_7_days: int
    pickups_last_30_days: int
    completed_last_7_days: int
    completed_last_30_days: int
    lots_listed: int
    lots_sold: int
    pending_dealer_applications: int


class PilotReliability(BaseModel):
    """Operational reliability signals we can compute from current source data.

    Fields that cannot be derived from authoritative state are returned as
    ``None`` together with an explicit ``available=False`` flag and a
    human-readable ``note`` so the UI can render "N/A" instead of misleading
    zeros. See docs/WIQ_V1_052_PILOT_METRICS.md for the full data audit.
    """

    api_error_rate: float | None
    api_error_rate_available: bool
    api_error_rate_note: str
    notification_failure_rate: float | None
    notification_failure_rate_available: bool
    notification_failure_rate_note: str
    background_job_failures: int | None
    background_job_failures_available: bool
    background_job_failures_note: str
    background_job_last_runs: dict[str, str | None]
    platform_uptime_seconds: float | None
    platform_uptime_available: bool
    platform_uptime_note: str


class PilotWindow(BaseModel):
    """The reporting window used for the pilot metrics snapshot."""

    start: str | None
    end: str | None
    days: int


class PilotMetrics(BaseModel):
    """Aggregated pilot metrics for the admin operational dashboard."""

    window: PilotWindow
    collection: PilotCollectionKpis
    timing: PilotTiming
    weight_quality: PilotWeightQuality
    activity: PilotActivity
    reliability: PilotReliability

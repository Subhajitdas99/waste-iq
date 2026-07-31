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

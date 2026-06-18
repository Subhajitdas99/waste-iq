from pydantic import BaseModel


class RoleBreakdown(BaseModel):
    citizens: int
    collectors: int
    admins: int


class RequestStatusBreakdown(BaseModel):
    pending: int
    accepted: int
    on_the_way: int
    collected: int
    completed: int
    cancelled: int


class AnalyticsRead(BaseModel):
    total_users: int
    total_pickup_requests: int
    total_completed_pickups: int
    total_collected_weight_kg: float
    users_by_role: RoleBreakdown
    requests_by_status: RequestStatusBreakdown

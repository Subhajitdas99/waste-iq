from fastapi import APIRouter

from app.api.routes import admin, auth, collector, pickup_requests

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(pickup_requests.router, prefix="/pickup-requests", tags=["Pickup Requests"])
api_router.include_router(collector.router, prefix="/collector", tags=["Collector"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])

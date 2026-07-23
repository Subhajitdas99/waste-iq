from fastapi import APIRouter

from app.api.routes import admin, auth, collector, dealer, inventory, pickup_requests

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(
    pickup_requests.router, prefix="/pickup-requests", tags=["Pickup Requests"]
)
api_router.include_router(collector.router, prefix="/collector", tags=["Collector"])
api_router.include_router(dealer.router, prefix="/dealer", tags=["Dealer"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])

# Inventory marketplace: same file, two routers, mounted under different
# prefixes since admin and dealer consume different endpoints from it.
api_router.include_router(inventory.admin_router, prefix="/admin", tags=["Admin Inventory"])
api_router.include_router(inventory.dealer_router, prefix="/dealer", tags=["Dealer Inventory"])

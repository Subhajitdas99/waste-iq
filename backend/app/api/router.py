from fastapi import APIRouter


from app.api.routes import admin
from app.api.routes import auth
from app.api.routes import collector
from app.api.routes import dealer
from app.api.routes import inventory
from app.api.routes import pickup_requests
from app.api.routes import jobs



from app.api.routes import (
    admin,
    analytics,
    auth,
    collector,
    collector_map,
    dealer,
    inventory,
    marketplace,
    notifications,
    pickup_requests,
)


api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

api_router.include_router(
    pickup_requests.router,
    prefix="/pickup-requests",
    tags=["Pickup Requests"],
)


api_router.include_router(
    collector.router,
    prefix="/collector",
    tags=["Collector"],
)

api_router.include_router(
    dealer.router,
    prefix="/dealer",
    tags=["Dealer"],
)

api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["Admin"],
)

# New Job Status endpoint
api_router.include_router(jobs.router)

api_router.include_router(collector.router, prefix="/collector", tags=["Collector"])
api_router.include_router(collector_map.router, prefix="/collector", tags=["Collector Map"])
api_router.include_router(dealer.router, prefix="/dealer", tags=["Dealer"])
api_router.include_router(marketplace.router, prefix="/marketplace", tags=["Marketplace"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(analytics.router, prefix="/admin/analytics", tags=["Admin Analytics"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])


# Inventory marketplace: same file, two routers, mounted under different
# prefixes since admin and dealer consume different endpoints from it.
api_router.include_router(
    inventory.admin_router,
    prefix="/admin",
    tags=["Admin Inventory"],
)

api_router.include_router(
    inventory.dealer_router,
    prefix="/dealer",
    tags=["Dealer Inventory"],
)
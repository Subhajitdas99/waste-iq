from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.db.session import engine

# Import SQLAlchemy Base
from app.models.base import Base

# Import all models so SQLAlchemy registers them
from app.models.user import User
from app.models.pickup_request import PickupRequest
from app.models.collector_assignment import CollectorAssignment

from app.services.auth import bootstrap_admin_user


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Create all database tables
    Base.metadata.create_all(bind=engine)

    # Create bootstrap admin account if configured
    bootstrap_admin_user()

    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Waste-IQ marketplace API for recyclable waste pickups.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["health"])
def healthcheck():
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": "1.0.0",
    }
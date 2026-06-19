from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

from app.services.auth import bootstrap_admin_user
from app.api.router import api_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Schema creation is owned by Alembic migrations.
    # Avoid create_all() here so local/dev databases do not drift into a
    # "tables exist but alembic history is missing" state.
    bootstrap_admin_user()
    yield


# FIX: Read cors_origins_list at call time, not at import time.
# Railway injects env vars before the process starts, but lru_cache
# can freeze a stale value if settings is imported before vars are set.
cors_origins = settings.cors_origins_list

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Waste-IQ marketplace API for recyclable waste pickups.",
    lifespan=lifespan,
)

# CRITICAL: CORSMiddleware MUST be added before include_router.
# Starlette applies middleware in reverse order — adding it after
# routers means it never wraps OPTIONS preflight requests.
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["health"])
def healthcheck():
    return {
        "status": "ok",
        "app": settings.app_name,
        "cors_origins": settings.cors_origins_list,
    }


# Temporary debug endpoint — remove after confirming CORS works
@app.get("/debug/cors", tags=["health"])
def debug_cors():
    return {
        "cors_origins_raw": settings.cors_origins,
        "cors_origins_list": settings.cors_origins_list,
        "loaded_into_middleware": cors_origins,
    }

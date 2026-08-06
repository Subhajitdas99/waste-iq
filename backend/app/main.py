from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import RequestIDMiddleware
from app.core.sentry_sdk import init_sentry
from app.services.auth import bootstrap_admin_user
from app.services.jobs import start_scheduler, stop_scheduler
from app.services.upload import (
    ImageUploadConfigurationError,
    ImageUploadUnavailableError,
)

# Configure logging
setup_logging(settings.log_level)

# Initialize Sentry
init_sentry()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Startup
    bootstrap_admin_user()
    start_scheduler()

    try:
        yield
    finally:
        # Shutdown
        stop_scheduler()


# Read CORS origins once at startup so the middleware and the /health
# endpoint always report the same allowlist for the lifetime of the process.
cors_origins = settings.cors_origins_list

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Waste-IQ marketplace API for recyclable waste pickups.",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(RequestIDMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(api_router)


@app.exception_handler(ImageUploadConfigurationError)
async def image_upload_configuration_error_handler(
    _: Request,
    exc: ImageUploadConfigurationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"detail": exc.detail},
    )


@app.exception_handler(ImageUploadUnavailableError)
async def image_upload_unavailable_error_handler(
    _: Request,
    exc: ImageUploadUnavailableError,
) -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content={"detail": exc.detail},
    )


@app.get("/health", tags=["health"])
def healthcheck() -> dict[str, object]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "cors_origins": settings.cors_origins_list,
    }



@app.get("/debug/cors", tags=["health"])
def debug_cors():
    return {
        "cors_origins_raw": settings.cors_origins,
        "cors_origins_list": settings.cors_origins_list,
        "loaded_into_middleware": cors_origins,
    }



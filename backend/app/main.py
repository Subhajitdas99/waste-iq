from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.router import api_router
from app.core.config import settings
from app.core.dependencies import get_db
from app.core.logging import setup_logging
from app.core.middleware import RequestIDMiddleware
from app.core.sentry_sdk import init_sentry
from app.services.auth import bootstrap_admin_user
from app.services.jobs import start_scheduler, stop_scheduler
from app.services.upload import ImageUploadConfigurationError, ImageUploadUnavailableError

# Configure logging
setup_logging(settings.log_level)

# Initialize Sentry
init_sentry()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Schema creation is owned by Alembic migrations.
    # Avoid create_all() here so local/dev databases do not drift into a
    # "tables exist but alembic history is missing" state.
    bootstrap_admin_user()
    start_scheduler()

    try:
        yield
    finally:
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

# Outermost middleware so the X-Request-ID header is set on every response,
# including CORS preflight responses.
app.add_middleware(RequestIDMiddleware)

app.include_router(api_router)

# Mount the local image storage directory only when the local production
# simulation fallback is active (WIQ-V1-054). The directory is backed by
# the ``uploads_data`` Docker volume in the simulation stack, so the
# mount survives container replacement. ``local_image_storage_active`` is
# gated on ``deployment_mode=local-simulation`` in config, so real
# production (deployment_mode=production) can NEVER mount this directory
# — Cloudinary (or another replicated object store) is the durable image
# storage strategy for production.
if settings.local_image_storage_active:
    uploads_path = Path(settings.local_image_storage_dir)
    uploads_path.mkdir(parents=True, exist_ok=True)
    app.mount(
        settings.local_image_storage_url_prefix,
        StaticFiles(directory=str(uploads_path)),
        name="local-uploads",
    )


@app.exception_handler(ImageUploadConfigurationError)
async def image_upload_configuration_error_handler(
    _: Request, exc: ImageUploadConfigurationError
) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": exc.detail})


@app.exception_handler(ImageUploadUnavailableError)
async def image_upload_unavailable_error_handler(
    _: Request, exc: ImageUploadUnavailableError
) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": exc.detail})


@app.get("/health", tags=["health"])
def healthcheck() -> dict[str, object]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "cors_origins": settings.cors_origins_list,
    }


@app.get("/health/ready", tags=["health"], response_model=None)
def readiness_check(db: Session = Depends(get_db)) -> dict[str, object] | JSONResponse:
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "app": settings.app_name,
                "reason": "database_unreachable",
            },
        )

    # Production requires a configured image storage provider. Cloudinary is
    # mandatory unless deployment_mode=local-simulation AND
    # LOCAL_IMAGE_STORAGE_ENABLED=true (enforced in config; the static file
    # mount and uploader selection are both gated on local_image_storage_active,
    # which can only be True when deployment_mode=local-simulation).
    # Configuration presence only — never a network call — so probes stay fast
    # and deterministic.
    if settings.cloudinary_required and not settings.cloudinary_configured:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "app": settings.app_name,
                "reason": "cloudinary_not_configured",
            },
        )

    return {
        "status": "ready",
        "app": settings.app_name,
    }

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings

from app.services.auth import bootstrap_admin_user
from app.api.router import api_router
from app.services.upload import ImageUploadConfigurationError, ImageUploadUnavailableError


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Schema creation is owned by Alembic migrations.
    # Avoid create_all() here so local/dev databases do not drift into a
    # "tables exist but alembic history is missing" state.
    bootstrap_admin_user()
    yield


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

app.include_router(api_router)


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

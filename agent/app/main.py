from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    if settings.agent_index_on_startup:
        import asyncio

        await asyncio.sleep(settings.agent_index_startup_delay_seconds)
        from app.api.dependencies import get_container

        try:
            get_container().pipeline().run()
        except Exception:  # noqa: BLE001 - startup indexing must not crash the app
            import logging

            logging.getLogger("agent").exception("startup indexing failed")
    yield


def create_app() -> FastAPI:
    setup_logging(settings.log_level)
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    if settings.agent_enable_request_id:
        from app.core.middleware import RequestIDMiddleware

        app.add_middleware(RequestIDMiddleware)
    app.include_router(api_router)
    return app


app = create_app()

from collections.abc import Generator
from pathlib import Path

from alembic import command
from alembic.config import Config as AlembicConfig
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

AGENT_DIR = Path(__file__).resolve().parents[2]

_connect_args: dict = {}
if settings.agent_database_url.startswith("sqlite"):
    _connect_args["check_same_thread"] = False
    _connect_args["timeout"] = 30

engine = create_engine(settings.agent_database_url, pool_pre_ping=True, connect_args=_connect_args)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def _alembic_config() -> AlembicConfig:
    """Programmatic Alembic config bound to the current settings database URL."""
    ini_path = AGENT_DIR / "alembic.ini"
    cfg = AlembicConfig(str(ini_path))
    cfg.set_main_option("script_location", str(AGENT_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", settings.agent_database_url)
    return cfg


def init_db() -> None:
    """Apply Alembic migrations (create_all is intentionally NOT used)."""
    command.upgrade(_alembic_config(), "head")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

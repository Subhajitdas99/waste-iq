import logging
from contextvars import ContextVar

_request_id: ContextVar[str] = ContextVar(
    "request_id",
    default="-",
)


class RequestIDFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id.get()
        return True


def set_request_id(request_id: str) -> None:
    _request_id.set(request_id)


def get_request_id() -> str:
    return _request_id.get()


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] [%(request_id)s] %(message)s",
    )
    for handler in logging.getLogger().handlers:
        handler.addFilter(RequestIDFilter())

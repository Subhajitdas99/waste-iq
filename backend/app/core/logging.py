import json
import logging
import logging.config
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


class JsonFormatter(logging.Formatter):
    """Formats every record as a single-line JSON object (stdlib only).

    Each line carries at minimum a timestamp, level, logger name, message and
    the active request id. ``extra`` fields are preserved and exception
    tracebacks are attached as an ``exception`` string. ``json.dumps`` with a
    ``str`` default guarantees the output is always valid JSON, even when a
    message or extra value contains quotes, newlines or exotic objects.
    """

    _EXCLUDED_FIELDS = frozenset(
        {
            "args",
            "asctime",
            "created",
            "exc_info",
            "exc_text",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "message",
            "msg",
            "name",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "taskName",
            "thread",
            "threadName",
        }
    )

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", get_request_id()),
        }

        if record.name == "uvicorn.access" and self._parse_access_args(payload, record):
            payload["event"] = "access"

        for key, value in record.__dict__.items():
            if key not in self._EXCLUDED_FIELDS and not key.startswith("_"):
                payload.setdefault(key, value)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)

    @staticmethod
    def _parse_access_args(payload: dict[str, object], record: logging.LogRecord) -> bool:
        """Structure Uvicorn access records.

        Uvicorn emits access lines as ``'%s - "%s %s HTTP/%s" %d'`` with the
        tuple ``(client_addr, method, path_with_query, http_version, status)``
        in ``record.args``. When that shape is recognised, structured fields
        are added; anything unexpected keeps the plain formatted message.
        """
        args = record.args
        if not isinstance(args, tuple) or len(args) != 5:
            return False

        client_addr, method, path, http_version, status_code = args
        payload["client_addr"] = client_addr
        payload["method"] = method
        payload["path"] = path
        payload["http_version"] = http_version
        payload["status_code"] = status_code
        return True


def setup_logging(level: str = "INFO") -> None:
    """Configure root and Uvicorn loggers to emit structured JSON logs.

    ``dictConfig`` fully reconfigures on every call so repeated invocations
    replace handlers instead of duplicating them. The three Uvicorn loggers
    share the JSON handler with propagation disabled — access and error lines
    therefore appear exactly once, already carry the active request id from
    the context var, and follow the same ``LOG_LEVEL`` as application logs.
    """

    effective_level = level.upper()

    config: dict[str, object] = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {"request_id": {"()": RequestIDFilter}},
        "formatters": {"json": {"()": JsonFormatter}},
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "filters": ["request_id"],
            },
        },
        "root": {"level": effective_level, "handlers": ["default"]},
        "loggers": {
            "uvicorn": {
                "level": effective_level,
                "handlers": ["default"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": effective_level,
                "handlers": ["default"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": effective_level,
                "handlers": ["default"],
                "propagate": False,
            },
        },
    }
    logging.config.dictConfig(config)

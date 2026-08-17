import json
import logging
import re

_SENSITIVE_PATTERN = re.compile(
    r"(?i)(secret|token|password|authorization|signature|x-hub-signature)"
    r'([":]=|"):\s*"?[^\s,"}"]+',
)


class RedactingFormatter(logging.Formatter):
    """Log formatter that masks known-sensitive values (tokens, secrets, keys)."""

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        return _SENSITIVE_PATTERN.sub(r"\1\2 [REDACTED]", message)


class JsonLogFormatter(logging.Formatter):
    """Structured JSON log formatter with sensitive-value redaction."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": self._redact(record.getMessage()),
        }
        if record.exc_info:
            entry["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str)

    @staticmethod
    def _redact(message: str) -> str:
        return _SENSITIVE_PATTERN.sub(r"\1\2 [REDACTED]", message)


def setup_logging(level: str = "INFO", structured: bool = False) -> None:
    handler = logging.StreamHandler()
    if structured:
        handler.setFormatter(JsonLogFormatter())
    else:
        handler.setFormatter(RedactingFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())

from contextvars import ContextVar

_ip_address: ContextVar[str | None] = ContextVar("ip_address", default=None)
_user_agent: ContextVar[str | None] = ContextVar("user_agent", default=None)


def set_request_metadata(ip_address: str | None, user_agent: str | None) -> None:
    _ip_address.set(ip_address)
    _user_agent.set(user_agent)


def get_request_ip() -> str | None:
    return _ip_address.get()


def get_request_user_agent() -> str | None:
    return _user_agent.get()

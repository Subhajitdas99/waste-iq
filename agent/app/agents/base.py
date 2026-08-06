"""Assistant registry — adding a new assistant must not touch existing agents."""

from __future__ import annotations

from typing import Any


class AssistantRegistry:
    _assistants: dict[str, Any] = {}

    @classmethod
    def register(cls, name: str, assistant: Any) -> None:
        cls._assistants[name] = assistant

    @classmethod
    def get(cls, name: str) -> Any | None:
        return cls._assistants.get(name)

    @classmethod
    def all(cls) -> dict[str, Any]:
        return dict(cls._assistants)

"""Strict JSON response parsing and Pydantic validation for LLM output.

Provider output is never trusted. It must parse as a single JSON object and
validate against the role schema (extra keys forbidden). Anything else is
rejected as `MalformedResponseError` before grounding is applied.
"""

from __future__ import annotations

import json
import re

from app.llm.models import (
    AnalyzeResponse,
    ExplainResponse,
    LLMRole,
    MalformedResponseError,
    SummarizeResponse,
)

ROLE_MODELS: dict[
    LLMRole,
    type[AnalyzeResponse] | type[ExplainResponse] | type[SummarizeResponse],
] = {
    "analyze": AnalyzeResponse,
    "explain": ExplainResponse,
    "summarize": SummarizeResponse,
}

_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


def extract_json(text: str) -> dict:
    """Extract the first JSON object from provider output.

    Accepts bare JSON, markdown-fenced JSON, and text with a JSON object
    embedded at the start. Trailing prose after the closing brace is ignored
    when the object itself is well-formed.
    """
    if not text or not text.strip():
        raise MalformedResponseError("empty provider response")
    cleaned = text.strip()
    fenced = _FENCE_RE.match(cleaned)
    if fenced:
        cleaned = fenced.group(1).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    start = cleaned.find("{")
    if start < 0:
        raise MalformedResponseError("provider response is not JSON")
    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(cleaned)):
        char = cleaned[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(cleaned[start : index + 1])
                except json.JSONDecodeError as exc:
                    raise MalformedResponseError(
                        f"provider response is not valid JSON: {exc}"
                    ) from exc
    raise MalformedResponseError("provider response contains no complete JSON object")


class ResponseParser:
    """Validates raw provider output against the role's Pydantic schema."""

    def parse(
        self, content: str, role: LLMRole
    ) -> AnalyzeResponse | ExplainResponse | SummarizeResponse:
        data = extract_json(content)
        model_class = ROLE_MODELS[role]
        try:
            return model_class.model_validate({**data, "role": role})
        except Exception as exc:  # noqa: BLE001 - pydantic ValidationError and friends
            raise MalformedResponseError(
                f"response failed schema validation for {role}: {exc}"
            ) from exc

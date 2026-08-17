"""Tests for strict JSON response parsing and schema validation."""

import pytest

from app.llm.models import MalformedResponseError
from app.llm.response_parser import ResponseParser, extract_json


def test_extract_json_bare():
    assert extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_fenced():
    text = '```json\n{"a": 1}\n```'
    assert extract_json(text) == {"a": 1}


def test_extract_json_embedded_in_prose():
    text = 'Here is the result: {"a": 1} and nothing else matters'
    assert extract_json(text) == {"a": 1}


def test_extract_json_ignores_trailing_prose():
    assert extract_json('{"a": {"b": [1, 2]}} trailing words') == {"a": {"b": [1, 2]}}


def test_extract_json_empty_raises():
    with pytest.raises(MalformedResponseError):
        extract_json("")


def test_extract_json_no_json_raises():
    with pytest.raises(MalformedResponseError):
        extract_json("just prose, no braces")


def test_extract_json_escaped_quotes_inside_string():
    text = 'prefix {"s": "escaped \\" quote"} trailing junk'
    assert extract_json(text) == {"s": 'escaped " quote'}


def test_extract_json_invalid_object_in_scan_raises():
    with pytest.raises(MalformedResponseError):
        extract_json('{"a": 1,} trailing')


def test_parse_analyze_success():
    content = '{"summary": "s", "priorities": ["p"], "confidence": 0.5, "references": []}'
    parsed = ResponseParser().parse(content, "analyze")
    assert parsed.role == "analyze"
    assert parsed.summary == "s"
    assert parsed.priorities == ["p"]


def test_parse_explain_success():
    content = '{"explanation": "because", "confidence": 0.9}'
    parsed = ResponseParser().parse(content, "explain")
    assert parsed.explanation == "because"


def test_parse_summarize_success():
    content = '{"overview": "o", "key_points": ["k1", "k2"]}'
    parsed = ResponseParser().parse(content, "summarize")
    assert parsed.overview == "o"
    assert parsed.key_points == ["k1", "k2"]


def test_parse_rejects_extra_keys():
    with pytest.raises(MalformedResponseError):
        ResponseParser().parse('{"summary": "s", "injected": 1}', "analyze")


def test_parse_rejects_role_mismatch():
    content = '{"summary": "s"}'  # analyze shape for explain role
    with pytest.raises(MalformedResponseError):
        ResponseParser().parse(content, "explain")


def test_parse_rejects_invalid_json():
    with pytest.raises(MalformedResponseError):
        ResponseParser().parse("not json at all", "analyze")


def test_parse_rejects_empty_content():
    with pytest.raises(MalformedResponseError):
        ResponseParser().parse("", "analyze")


def test_parse_accepts_fenced_mock_style_output():
    content = '```\n{"overview": "o", "key_points": ["k"]}\n```'
    parsed = ResponseParser().parse(content, "summarize")
    assert parsed.overview == "o"

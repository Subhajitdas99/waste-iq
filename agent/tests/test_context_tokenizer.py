"""Tokenizer unit tests: singular/plural query expansion."""

from app.context.tokenizer import (
    expand_query_tokens,
    singularize,
    unique_subword_tokens,
)


def test_singularize_strips_plural_s():
    assert singularize("notifications") == "notification"
    assert singularize("dealers") == "dealer"
    assert singularize("tokens") == "token"


def test_singularize_skips_unsafe_endings():
    assert singularize("class") == "class"
    assert singularize("status") == "status"
    assert singularize("is") == "is"
    assert singularize("to") == "to"


def test_expand_query_tokens_adds_singular_variant():
    assert expand_query_tokens("refresh notifications") == [
        "refresh",
        "notifications",
        "notification",
    ]


def test_expand_query_tokens_does_not_add_plurals():
    assert expand_query_tokens("refresh token") == ["refresh", "token"]


def test_expand_query_tokens_deduplicates():
    tokens = expand_query_tokens("notifications notification")
    assert tokens.count("notification") == 1
    assert tokens[0] == "notifications"
    assert tokens[1] == "notification"


def test_unique_subword_tokens_unchanged():
    assert unique_subword_tokens("notifications") == ["notifications"]

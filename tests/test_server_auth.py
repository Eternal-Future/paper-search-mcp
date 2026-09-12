"""Deterministic tests for the streamable-http auth wiring (no network access)."""

import asyncio

import pytest

from paper_search_mcp import server


def _verify(token: str, expected: str = "s3cret"):
    verifier = server.StaticTokenVerifier(expected)
    return asyncio.run(verifier.verify_token(token))


def test_verifier_accepts_matching_token():
    result = _verify("s3cret")
    assert result is not None
    assert result.token == "s3cret"
    assert result.client_id == "paper-search-mcp"
    assert result.scopes == []


def test_verifier_rejects_wrong_token():
    assert _verify("nope") is None


def test_verifier_rejects_empty_token():
    assert _verify("") is None


@pytest.mark.parametrize(
    "env_value,expected",
    [
        ("", "stdio"),
        ("stdio", "stdio"),
        ("STDIO", "stdio"),
        ("streamable-http", "streamable-http"),
    ],
)
def test_resolve_transport(monkeypatch, env_value, expected):
    monkeypatch.setattr(server, "get_env", lambda name, default="": env_value)
    assert server.resolve_transport() == expected


def test_resolve_transport_defaults_to_stdio(monkeypatch):
    monkeypatch.setattr(server, "get_env", lambda name, default="": default)
    assert server.resolve_transport() == "stdio"


def test_resolve_transport_rejects_unknown(monkeypatch):
    monkeypatch.setattr(server, "get_env", lambda name, default="": "sse")
    with pytest.raises(ValueError):
        server.resolve_transport()


@pytest.mark.parametrize(
    "env_value,expected",
    [
        ("true", True),
        ("TRUE", True),
        ("1", True),
        ("yes", True),
        ("on", True),
        ("", True),
        ("false", False),
        ("0", False),
        ("no", False),
        ("off", False),
        ("garbage", True),
    ],
)
def test_resolve_http_stateless(monkeypatch, env_value, expected):
    monkeypatch.setattr(
        server, "get_env", lambda name, default="": env_value if name == "HTTP_STATELESS" else default
    )
    assert server._resolve_http_stateless() is expected
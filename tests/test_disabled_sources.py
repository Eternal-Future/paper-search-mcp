"""Deterministic tests for platform disabling and date serialization (no network)."""

import asyncio
from datetime import datetime

import pytest

from paper_search_mcp import cli, config, server
from paper_search_mcp.paper import Paper


# --- PAPER_SEARCH_MCP_DISABLED_SOURCES parsing ---


def test_config_disabled_sources_parses_csv(monkeypatch):
    monkeypatch.setattr(
        config,
        "get_env",
        lambda name, default="": " zenodo , HAL,,zenodo" if name == "DISABLED_SOURCES" else default,
    )
    assert config.disabled_sources() == {"zenodo", "hal"}


def test_config_disabled_sources_empty_by_default(monkeypatch):
    monkeypatch.setattr(config, "get_env", lambda name, default="": default)
    assert config.disabled_sources() == set()


# --- server-side filtering ---


def test_parse_sources_excludes_disabled_from_all(monkeypatch):
    monkeypatch.setattr(server, "_disabled_sources", {"zenodo", "hal"})
    selected = server._parse_sources("all")
    assert "zenodo" not in selected
    assert "hal" not in selected
    assert "arxiv" in selected


def test_parse_sources_drops_explicitly_disabled(monkeypatch):
    monkeypatch.setattr(server, "_disabled_sources", {"zenodo"})
    assert server._parse_sources("arxiv,zenodo") == ["arxiv"]


# --- per-tool guard ---


def test_guard_blocks_disabled_source(monkeypatch):
    monkeypatch.setattr(server, "_disabled_sources", {"zenodo"})
    calls = []

    async def fake_search():
        calls.append(1)
        return []

    guarded = server._guard_disabled("zenodo")(fake_search)
    with pytest.raises(RuntimeError, match="disabled"):
        asyncio.run(guarded())

    assert calls == []


def test_guard_allows_enabled_source(monkeypatch):
    monkeypatch.setattr(server, "_disabled_sources", set())

    async def fake_search():
        return ["ok"]

    guarded = server._guard_disabled("arxiv")(fake_search)
    assert asyncio.run(guarded()) == ["ok"]


# --- CLI filtering ---


def test_cli_parse_sources_excludes_disabled(monkeypatch):
    # SEARCHERS is lazily built; stub it to keep this test network-free.
    monkeypatch.setattr(cli, "SEARCHERS", {"arxiv": object(), "hal": object()})
    monkeypatch.setattr(cli, "disabled_sources", lambda: {"hal"})
    assert cli._parse_sources("arxiv,hal") == ["arxiv"]


# --- Paper date serialization (Zenodo/HAL pass string dates) ---


def test_paper_to_dict_handles_string_dates():
    paper = Paper(
        paper_id="p1",
        title="t",
        authors=["a"],
        abstract="",
        doi="",
        published_date="2024-01-15",
        pdf_url="",
        url="",
        source="zenodo",
    )
    assert paper.to_dict()["published_date"] == "2024-01-15"


def test_paper_to_dict_handles_none_dates():
    paper = Paper(
        paper_id="p1",
        title="t",
        authors=["a"],
        abstract="",
        doi="",
        published_date=None,
        pdf_url="",
        url="",
        source="hal",
    )
    assert paper.to_dict()["published_date"] == ""


def test_paper_to_dict_handles_datetime_dates():
    paper = Paper(
        paper_id="p1",
        title="t",
        authors=["a"],
        abstract="",
        doi="",
        published_date=datetime(2024, 1, 15),
        pdf_url="",
        url="",
        source="arxiv",
    )
    assert paper.to_dict()["published_date"] == "2024-01-15T00:00:00"
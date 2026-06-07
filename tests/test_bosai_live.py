"""
Live smoke test against the real JMA bosai feed (Atom XML).

These tests are intentionally optional and do NOT run in the default offline suite
(tests/ -v). They require actual internet connectivity.

Usage:
    .venv/bin/pytest tests/test_bosai_live.py -v

Implementation note:
    pytest-homeassistant-custom-component blocks all external sockets via two mechanisms:
      1. socket.socket constructor → GuardedSocket (blocks creation)
      2. socket.socket.connect    → guarded_connect (blocks by IP)
    Both are captured at pytest_socket import time in _true_socket / _true_connect.
    This test temporarily restores both for the duration of the HTTP calls, then
    reinstates the guards so subsequent tests in the same session are not affected.
"""
import socket

import aiohttp
import pytest
import pytest_socket

from custom_components.jma_weather.bosai_feed import parse_feed, relevant_entries
from custom_components.jma_weather.const import BOSAI_FEED_URL


@pytest.mark.asyncio
async def test_live_feed_parses():
    # Save the current (guarded) state so we can restore it after.
    _guarded_socket = socket.socket
    _guarded_connect = socket.socket.connect
    _guarded_getaddrinfo = socket.getaddrinfo

    # Restore real implementations captured by pytest_socket at import time.
    socket.socket = pytest_socket._true_socket  # type: ignore[assignment]
    socket.socket.connect = pytest_socket._true_connect  # type: ignore[assignment]

    # Also patch using pytest_socket's own enable function for completeness.
    pytest_socket.enable_socket()

    # Restore real getaddrinfo captured by the HA plugin.
    try:
        from pytest_homeassistant_custom_component import plugins as _ha_plugins
        _real_getaddrinfo = _ha_plugins._real_getaddrinfo
        socket.getaddrinfo = _real_getaddrinfo  # type: ignore[assignment]
    except (ImportError, AttributeError):
        pass  # fall back to whatever is currently set

    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(BOSAI_FEED_URL) as r:
                text = await r.text()
    finally:
        # Restore guards so subsequent tests are not affected.
        socket.socket = _guarded_socket  # type: ignore[assignment]
        socket.socket.connect = _guarded_connect  # type: ignore[assignment]
        socket.getaddrinfo = _guarded_getaddrinfo  # type: ignore[assignment]

    entries = parse_feed(text)
    assert len(entries) > 0
    assert all(e["product"] and e["office"] and e["url"] for e in entries)
    rel = relevant_entries(entries, "400000")
    assert isinstance(rel, list)

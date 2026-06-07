"""
Live smoke test against the real JMA warning R06 feed (VPWS50 XML).

These tests are intentionally optional and do NOT run in the default offline suite
(tests/ -v). They require actual internet connectivity.

Usage:
    .venv/bin/pytest tests/test_warning_r06_live.py -v

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

from custom_components.jma_weather.bosai_feed import parse_feed
from custom_components.jma_weather.const import PRODUCT_SHUYAKU, WARNING_FEED_URL
from custom_components.jma_weather.warning_r06 import parse_warnings_r06


@pytest.mark.asyncio
async def test_live_shuyaku_parses():
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
            async with s.get(WARNING_FEED_URL) as r:
                feed = await r.text()
            ents = [e for e in parse_feed(feed) if e["product"] == PRODUCT_SHUYAKU]
            assert ents, "VPWS50 が regular feed に無い"
            latest = max(ents, key=lambda e: e["updated"])
            async with s.get(latest["url"]) as r:
                xml = await r.text()
    finally:
        # Restore guards so subsequent tests are not affected.
        socket.socket = _guarded_socket  # type: ignore[assignment]
        socket.socket.connect = _guarded_connect  # type: ignore[assignment]
        socket.getaddrinfo = _guarded_getaddrinfo  # type: ignore[assignment]

    res = parse_warnings_r06(xml, {"4044700", "4420200"})
    assert set(res) == {"4044700", "4420200"}
    for v in res.values():
        assert "warnings" in v and "max_level" in v and "count" in v

    # Print live data for 別府市 (4420200) for inspection
    beppu = res.get("4420200", {})
    print(f"\n[LIVE] 別府市 (4420200): {beppu}")

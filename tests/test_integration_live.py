"""
Live smoke test against the real JMA API.

These tests are intentionally optional and do NOT run in the default offline suite
(tests/ -v). They require actual internet connectivity.

Usage:
    .venv/bin/pytest tests/test_integration_live.py -v

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

from custom_components.jma_weather.area import fetch_area, resolve_class10
from custom_components.jma_weather.coordinator import WARNING_URL
from custom_components.jma_weather.jma_parse import parse_warnings


@pytest.mark.asyncio
async def test_live_fukuoka() -> None:
    """
    筑前町 (4044700) の class10 解決 + 福岡県 (400000) の警報 API 疎通確認。

    実際の area.json での親チェーン:
        4044700 (筑前町) → 400041 (筑後北部/class15) → 400040 (class10)

    class10 は 400040 が正。{"400040", "400041", "400010"} に含まれることを確認する。
    """
    # Save the current (guarded) state so we can restore it after.
    _guarded_socket = socket.socket
    _guarded_connect = socket.socket.connect
    _guarded_getaddrinfo = socket.getaddrinfo

    # Restore real implementations captured by pytest_socket at import time.
    socket.socket = pytest_socket._true_socket  # type: ignore[assignment]
    socket.socket.connect = pytest_socket._true_connect  # type: ignore[assignment]
    socket.getaddrinfo = socket._real_getaddrinfo if hasattr(socket, "_real_getaddrinfo") else _guarded_getaddrinfo  # type: ignore[assignment]

    # Also patch using pytest_socket's own enable function for completeness.
    pytest_socket.enable_socket()

    # Resolve DNS before restoring guards — use the system resolver directly.
    import socket as _sock_mod
    # Use the true getaddrinfo captured by pytest_socket (stored in the HA plugin).
    # The HA plugins.py stores it as _real_getaddrinfo in its module scope.
    try:
        from pytest_homeassistant_custom_component import plugins as _ha_plugins
        _real_getaddrinfo = _ha_plugins._real_getaddrinfo
        socket.getaddrinfo = _real_getaddrinfo  # type: ignore[assignment]
    except (ImportError, AttributeError):
        pass  # fall back to whatever is currently set

    try:
        async with aiohttp.ClientSession() as s:
            area = await fetch_area(s)
            actual_class10 = resolve_class10(area, "4044700")
            # Real resolved value is 400040 (confirmed against live area.json 2026-06-07).
            # Parent chain: 4044700 (筑前町/class20) → 400041 (筑後北部/class15) → 400040 (class10)
            # The set also covers alternative codes in case the JMA structure changes.
            assert actual_class10 in {"400040", "400041", "400010"}, (
                f"resolve_class10 returned unexpected value: {actual_class10!r}. "
                "If JMA area structure changed, update the assertion set to the actual value."
            )

            async with s.get(WARNING_URL.format(office="400000")) as r:
                assert r.status == 200, f"JMA warning API returned HTTP {r.status}"
                payload = await r.json()
    finally:
        # Restore guards so subsequent tests are not affected.
        socket.socket = _guarded_socket  # type: ignore[assignment]
        socket.socket.connect = _guarded_connect  # type: ignore[assignment]
        socket.getaddrinfo = _guarded_getaddrinfo  # type: ignore[assignment]

    result = parse_warnings(payload, "4044700")
    assert "count" in result, "parse_warnings result missing 'count'"
    assert "summary" in result, "parse_warnings result missing 'summary'"
    assert "area_found" in result, "parse_warnings result missing 'area_found'"
    assert result["area_found"] is True, (
        f"4044700 not found in office 400000 response. Full result: {result}"
    )
    # count can be 0 (no active warnings) or positive — both are valid
    assert isinstance(result["count"], int) and result["count"] >= 0

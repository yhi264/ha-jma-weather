import json
import pathlib

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.jma_weather.coordinator import JmaWarningCoordinator

FIX = pathlib.Path(__file__).parent / "fixtures"


class _FakeResp:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status = status

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    def raise_for_status(self):
        if self.status != 200:
            raise Exception("http error")

    async def json(self):
        return self._payload


class _FakeSession:
    def __init__(self, payload, status=200):
        self._payload = payload
        self._status = status

    def get(self, url, **kw):
        return _FakeResp(self._payload, self._status)


async def test_coordinator_parses(hass):
    payload = json.loads((FIX / "warning_multi.json").read_text(encoding="utf-8"))
    coord = JmaWarningCoordinator(
        hass, session=_FakeSession(payload),
        office_code="400000", class20_code="4044700", scan_interval=300,
    )
    data = await coord._async_update_data()
    assert data["count"] == 2
    assert data["has_special_warning"] is False


async def test_coordinator_http_error_raises_updatefailed(hass):
    coord = JmaWarningCoordinator(
        hass, session=_FakeSession({}, status=500),
        office_code="400000", class20_code="4044700", scan_interval=300,
    )
    with pytest.raises(UpdateFailed):
        await coord._async_update_data()

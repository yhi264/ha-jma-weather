import datetime as dt
import pathlib
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.jma_weather.coordinator import JmaBosaiFeedCoordinator

FIX = pathlib.Path(__file__).parent / "fixtures"


def _text(name):
    return (FIX / name).read_text(encoding="utf-8")


async def test_bosai_coordinator_builds_states(hass):
    feed = _text("extra_min.xml")
    bodies = {
        "VXWW50": _text("doshakei_active.xml"),
        "VPHW50": _text("tatsumaki_active.xml"),
        "VPFJ50": _text("fuken_kiroku.xml"),
    }

    async def fake_get_text(url: str) -> str:
        if url.endswith("extra.xml"):
            return feed
        for prod, body in bodies.items():
            if f"_{prod}_" in url:
                return body
        raise AssertionError(url)

    coord = JmaBosaiFeedCoordinator(
        hass, session=None, office_code="400000", class20_code="4044700",
        scan_interval=300,
    )
    fixed_now = dt.datetime(2026, 6, 7, 12, 40, tzinfo=dt.timezone(dt.timedelta(hours=9)))
    with patch.object(coord, "_fetch_text", side_effect=fake_get_text), \
         patch.object(coord, "_now", return_value=fixed_now):
        data = await coord._async_update_data()

    assert data["doshakei"]["active"] is True
    assert data["tatsumaki"]["active"] is True
    assert data["kirokuame"]["active"] is True


async def test_bosai_coordinator_feed_error_raises(hass):
    coord = JmaBosaiFeedCoordinator(
        hass, session=None, office_code="400000", class20_code="4044700",
        scan_interval=300,
    )
    with patch.object(coord, "_fetch_text", AsyncMock(side_effect=Exception("net"))):
        with pytest.raises(UpdateFailed):
            await coord._async_update_data()

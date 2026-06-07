import pathlib
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.jma_weather.coordinator import JmaWarningCoordinator

FIX = pathlib.Path(__file__).parent / "fixtures"
XML = (FIX / "warning_shuyaku_min.xml").read_text(encoding="utf-8")

FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry><title>気象警報・注意報（Ｒ０６）（集約通報）</title>
    <id>https://www.data.jma.go.jp/developer/xml/data/20260607T2050_0_VPWS50_010000.xml</id>
    <updated>2026-06-07T11:50:00Z</updated><content>x</content></entry>
</feed>"""


async def test_coordinator_parses_registered_areas(hass):
    coord = JmaWarningCoordinator(hass, session=None, scan_interval=300)
    coord.register_area("4044700")
    coord.register_area("4420200")

    async def fake_fetch(url):
        return FEED if url.endswith("regular.xml") else XML

    with patch.object(coord, "_fetch_text", side_effect=fake_fetch):
        data = await coord._async_update_data()
    assert data["4044700"]["count"] == 2
    assert data["4420200"]["warnings"][0]["code"] == "16"
    assert "4720100" not in data


async def test_coordinator_feed_error(hass):
    coord = JmaWarningCoordinator(hass, session=None, scan_interval=300)
    coord.register_area("4044700")
    with patch.object(coord, "_fetch_text", AsyncMock(side_effect=Exception("net"))):
        with pytest.raises(UpdateFailed):
            await coord._async_update_data()


def test_register_unregister(hass):
    coord = JmaWarningCoordinator(hass, session=None, scan_interval=300)
    coord.register_area("4044700")
    assert coord.has_areas() is True
    coord.unregister_area("4044700")
    assert coord.has_areas() is False

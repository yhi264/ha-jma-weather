import json
import pathlib
from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.jma_weather.const import (
    DOMAIN, CONF_OFFICE, CONF_CLASS20, CONF_CLASS10, CONF_AREA_NAME,
)

FIX = pathlib.Path(__file__).parent / "fixtures"


async def test_setup_and_unload(hass):
    payload = json.loads((FIX / "warning_multi.json").read_text(encoding="utf-8"))
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="JMA 筑前町",
        unique_id="4044700",
        data={
            CONF_OFFICE: "400000", CONF_CLASS20: "4044700",
            CONF_CLASS10: "400040", CONF_AREA_NAME: "筑前町",
        },
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.jma_weather.coordinator.JmaWarningCoordinator._async_update_data",
        return_value={
            "warnings": [{"code": "14", "name": "雷注意報", "level": "注意報", "status": "発表"}],
            "count": 1, "summary": "雷注意報", "has_special_warning": False,
            "report_datetime": "2026-06-07T05:00:00+09:00", "area_found": True,
        },
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.state is ConfigEntryState.LOADED

        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.state is ConfigEntryState.NOT_LOADED

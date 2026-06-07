from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.jma_weather.const import (
    DOMAIN, CONF_OFFICE, CONF_CLASS20, CONF_CLASS10, CONF_AREA_NAME,
)

_W = {"4044700": {"warnings": [], "count": 0, "summary": "なし",
                  "has_special_warning": False, "max_level": None, "report_datetime": ""},
      "4420200": {"warnings": [], "count": 0, "summary": "なし",
                  "has_special_warning": False, "max_level": None, "report_datetime": ""}}
_BOSAI = {"doshakei": {"active": False, "info_type": "", "report_datetime": "", "headline": "", "target_areas": []},
          "tatsumaki": {"active": False, "info_type": "", "report_datetime": "", "headline": "", "valid_until": ""},
          "kirokuame": {"active": False, "info_type": "", "report_datetime": "", "headline": ""}}


def _entry(class20):
    return MockConfigEntry(
        domain=DOMAIN, title=f"JMA {class20}", unique_id=class20,
        data={CONF_OFFICE: "400000", CONF_CLASS20: class20,
              CONF_CLASS10: "400040", CONF_AREA_NAME: "地点"},
    )


async def test_two_entries_share_one_warning_coordinator(hass):
    e1 = _entry("4044700"); e1.add_to_hass(hass)
    e2 = _entry("4420200"); e2.add_to_hass(hass)
    with patch(
        "custom_components.jma_weather.coordinator.JmaWarningCoordinator._async_update_data",
        return_value=_W,
    ), patch(
        "custom_components.jma_weather.coordinator.JmaBosaiFeedCoordinator._async_update_data",
        return_value=_BOSAI,
    ):
        # HA sets up all entries in the domain when the first is set up
        assert await hass.config_entries.async_setup(e1.entry_id)
        await hass.async_block_till_done()
        # e2 is set up automatically when integration initialises
        assert e1.state is ConfigEntryState.LOADED
        assert e2.state is ConfigEntryState.LOADED

        assert e1.runtime_data.warning is e2.runtime_data.warning  # 共有
        shared = e1.runtime_data.warning
        assert {"4044700", "4420200"}.issubset(shared._areas)

        assert await hass.config_entries.async_unload(e1.entry_id)
        await hass.async_block_till_done()
        assert "4044700" not in shared._areas
        assert shared.has_areas() is True

        assert await hass.config_entries.async_unload(e2.entry_id)
        await hass.async_block_till_done()
        assert hass.data.get(DOMAIN, {}).get("warning") is None

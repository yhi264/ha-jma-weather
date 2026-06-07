from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.jma_weather.const import (
    DOMAIN, CONF_OFFICE, CONF_CLASS20, CONF_CLASS10, CONF_AREA_NAME,
)

_WARN = {"warnings": [], "count": 0, "summary": "なし",
         "has_special_warning": False, "report_datetime": "", "area_found": True}
_BOSAI = {
    "doshakei": {"active": False, "info_type": "", "report_datetime": "", "headline": "", "target_areas": []},
    "tatsumaki": {"active": False, "info_type": "", "report_datetime": "", "headline": "", "valid_until": ""},
    "kirokuame": {"active": False, "info_type": "", "report_datetime": "", "headline": ""},
}


async def test_bosai_feed_failure_still_loads_entry(hass):
    """bosai フィード取得が失敗しても entry は LOADED（2a 警報は生きる）。"""
    from homeassistant.helpers.update_coordinator import UpdateFailed
    entry = MockConfigEntry(
        domain=DOMAIN, title="JMA 筑前町", unique_id="4044700",
        data={CONF_OFFICE: "400000", CONF_CLASS20: "4044700",
              CONF_CLASS10: "400040", CONF_AREA_NAME: "筑前町"},
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.jma_weather.coordinator.JmaWarningCoordinator._async_update_data",
        return_value=_WARN,
    ), patch(
        "custom_components.jma_weather.coordinator.JmaBosaiFeedCoordinator._async_update_data",
        side_effect=UpdateFailed("feed down"),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.state is ConfigEntryState.LOADED
        assert entry.runtime_data.bosai is not None
        # 警報(集約)センサーは生きている
        assert hass.states.get("sensor.jma_weather_4044700_warnings") is not None


async def test_setup_creates_both_coordinators(hass):
    entry = MockConfigEntry(
        domain=DOMAIN, title="JMA 筑前町", unique_id="4044700",
        data={CONF_OFFICE: "400000", CONF_CLASS20: "4044700",
              CONF_CLASS10: "400040", CONF_AREA_NAME: "筑前町"},
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.jma_weather.coordinator.JmaWarningCoordinator._async_update_data",
        return_value=_WARN,
    ), patch(
        "custom_components.jma_weather.coordinator.JmaBosaiFeedCoordinator._async_update_data",
        return_value=_BOSAI,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.state is ConfigEntryState.LOADED
        assert entry.runtime_data.warning is not None
        assert entry.runtime_data.bosai is not None

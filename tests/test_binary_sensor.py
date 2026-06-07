from unittest.mock import patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.jma_weather.const import (
    DOMAIN, CONF_OFFICE, CONF_CLASS20, CONF_CLASS10, CONF_AREA_NAME,
)

_W = {"4044700": {
    "warnings": [
        {"code": "10", "name": "大雨注意報", "level": 2, "status": "継続"},
    ],
    "count": 1, "summary": "大雨注意報", "has_special_warning": False,
    "max_level": 2, "report_datetime": "2026-06-07T20:50:00+09:00",
}}
_BOSAI = {"doshakei": {"active": False, "info_type": "", "report_datetime": "", "headline": "", "target_areas": []},
          "tatsumaki": {"active": False, "info_type": "", "report_datetime": "", "headline": "", "valid_until": ""},
          "kirokuame": {"active": False, "info_type": "", "report_datetime": "", "headline": ""}}


async def _setup(hass):
    entry = MockConfigEntry(
        domain=DOMAIN, title="JMA 筑前町", unique_id="4044700",
        data={CONF_OFFICE: "400000", CONF_CLASS20: "4044700",
              CONF_CLASS10: "400040", CONF_AREA_NAME: "筑前町"},
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.jma_weather.coordinator.JmaWarningCoordinator._async_update_data",
        return_value=_W,
    ), patch(
        "custom_components.jma_weather.coordinator.JmaBosaiFeedCoordinator._async_update_data",
        return_value=_BOSAI,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


async def test_ooame_on_with_level(hass):
    await _setup(hass)
    state = hass.states.get("binary_sensor.jma_weather_4044700_ooame")
    assert state is not None
    assert state.state == "on"
    assert state.attributes["level"] == 2
    assert state.attributes["status"] == "継続"


async def test_kaminari_off(hass):
    await _setup(hass)
    state = hass.states.get("binary_sensor.jma_weather_4044700_kaminari")
    assert state is not None
    assert state.state == "off"
    assert state.attributes["level"] is None


async def test_minor_phenomenon_enabled(hass):
    await _setup(hass)
    assert hass.states.get("binary_sensor.jma_weather_4044700_kansou") is not None

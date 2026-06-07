from unittest.mock import patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.jma_weather.const import (
    DOMAIN, CONF_OFFICE, CONF_CLASS20, CONF_CLASS10, CONF_AREA_NAME,
)

_W = {"4044700": {
    "warnings": [
        {"code": "10", "name": "大雨注意報", "level": 2, "status": "継続"},
        {"code": "14", "name": "雷注意報", "level": None, "status": "発表"},
    ],
    "count": 2, "summary": "大雨注意報・雷注意報", "has_special_warning": False,
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


async def test_aggregate_sensor_with_level(hass):
    await _setup(hass)
    state = hass.states.get("sensor.jma_weather_4044700_warnings")
    assert state is not None
    assert state.state == "2"
    assert state.attributes["summary"] == "大雨注意報・雷注意報"
    assert state.attributes["max_level"] == 2
    assert state.attributes["area_name"] == "筑前町"
    w = {x["code"]: x for x in state.attributes["warnings"]}
    assert w["10"]["level"] == 2
    assert w["14"]["level"] is None

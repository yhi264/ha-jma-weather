from unittest.mock import patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.jma_weather.const import (
    DOMAIN, CONF_OFFICE, CONF_CLASS20, CONF_CLASS10, CONF_AREA_NAME,
)

_WARN = {"warnings": [], "count": 0, "summary": "なし",
         "has_special_warning": False, "report_datetime": "", "area_found": True}
_BOSAI = {
    "doshakei": {"active": True, "info_type": "発表", "report_datetime": "2026-06-07T12:30:00+09:00",
                 "headline": "福岡県土砂災害警戒情報", "target_areas": ["筑前町", "朝倉市"]},
    "tatsumaki": {"active": False, "info_type": "", "report_datetime": "", "headline": "", "valid_until": ""},
    "kirokuame": {"active": False, "info_type": "", "report_datetime": "", "headline": ""},
}


async def _setup(hass):
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
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


async def test_doshakei_on_with_attrs(hass):
    await _setup(hass)
    state = hass.states.get("binary_sensor.jma_weather_4044700_doshakei")
    assert state is not None
    assert state.state == "on"
    assert state.attributes["info_type"] == "発表"
    assert "筑前町" in state.attributes["target_areas"]


async def test_tatsumaki_off(hass):
    await _setup(hass)
    state = hass.states.get("binary_sensor.jma_weather_4044700_tatsumaki")
    assert state is not None
    assert state.state == "off"


async def test_kirokuame_present(hass):
    await _setup(hass)
    assert hass.states.get("binary_sensor.jma_weather_4044700_kirokuame") is not None

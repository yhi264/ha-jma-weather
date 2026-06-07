from unittest.mock import patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.jma_weather.const import (
    DOMAIN, CONF_OFFICE, CONF_CLASS20, CONF_CLASS10, CONF_AREA_NAME,
)

_DATA = {
    "warnings": [
        {"code": "14", "name": "雷注意報", "level": "注意報", "status": "発表"},
    ],
    "count": 1, "summary": "雷注意報", "has_special_warning": False,
    "report_datetime": "2026-06-07T05:00:00+09:00", "area_found": True,
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
        return_value=_DATA,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


async def test_kaminari_on(hass):
    await _setup(hass)
    # 明示的 entity_id（ASCII・安定）
    state = hass.states.get("binary_sensor.jma_weather_4044700_kaminari")
    assert state is not None
    assert state.state == "on"
    assert state.attributes["level"] == "注意報"
    assert state.attributes["status"] == "発表"
    # 大雨は出ていないので off
    ooame = hass.states.get("binary_sensor.jma_weather_4044700_ooame")
    assert ooame is not None
    assert ooame.state == "off"


async def test_minor_phenomena_disabled_by_default(hass):
    await _setup(hass)
    # 乾燥(kansou)は enabled_default=False → state 取得不可（登録のみ・無効）
    assert hass.states.get("binary_sensor.jma_weather_4044700_kansou") is None

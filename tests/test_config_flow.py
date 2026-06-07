import json
import pathlib
from unittest.mock import patch

from homeassistant.data_entry_flow import FlowResultType

from custom_components.jma_weather.const import DOMAIN, CONF_OFFICE, CONF_CLASS20

FIX = pathlib.Path(__file__).parent / "fixtures"
AREA = json.loads((FIX / "area_min.json").read_text(encoding="utf-8"))


async def test_full_flow(hass):
    with patch("custom_components.jma_weather.config_flow.fetch_area", return_value=AREA), \
         patch("custom_components.jma_weather.config_flow._test_warning", return_value=True):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "office"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_OFFICE: "400000"}
        )
        assert result["step_id"] == "municipality"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_CLASS20: "4044700"}
        )
        # 座標確認ステップ
        assert result["step_id"] == "location"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"latitude": 33.5, "longitude": 130.6}
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_CLASS20] == "4044700"
        assert result["data"]["class10_code"] == "400040"


async def test_duplicate_aborts(hass):
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    MockConfigEntry(domain=DOMAIN, unique_id="4044700", data={}).add_to_hass(hass)
    with patch("custom_components.jma_weather.config_flow.fetch_area", return_value=AREA), \
         patch("custom_components.jma_weather.config_flow._test_warning", return_value=True):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_OFFICE: "400000"})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_CLASS20: "4044700"})
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "already_configured"


async def test_options_flow(hass):
    from unittest.mock import patch
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from custom_components.jma_weather.const import CONF_SCAN_INTERVAL

    entry = MockConfigEntry(
        domain=DOMAIN, unique_id="4044700",
        data={CONF_OFFICE: "400000", CONF_CLASS20: "4044700",
              "class10_code": "400040", "area_name": "筑前町",
              "latitude": 33.5, "longitude": 130.6},
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.jma_weather.coordinator.JmaWarningCoordinator._async_update_data",
        return_value={"warnings": [], "count": 0, "summary": "なし",
                      "has_special_warning": False, "report_datetime": "", "area_found": True},
    ):
        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["step_id"] == "init"
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {CONF_SCAN_INTERVAL: 600}
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_SCAN_INTERVAL] == 600

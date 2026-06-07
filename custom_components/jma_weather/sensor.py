"""集約 sensor: 発表中の警報件数 + 詳細属性（共有コーディネーター参照）。"""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import JmaConfigEntry
from .const import CONF_AREA_NAME, CONF_CLASS20, DOMAIN
from .device import jma_device_info

_EMPTY = {"count": 0, "summary": "なし", "warnings": [],
          "has_special_warning": False, "max_level": None, "report_datetime": ""}


async def async_setup_entry(
    hass: HomeAssistant, entry: JmaConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([JmaWarningCountSensor(entry)])


class JmaWarningCountSensor(CoordinatorEntity, SensorEntity):
    """発表中の警報・注意報件数。"""

    _attr_has_entity_name = True
    _attr_name = "警報注意報"
    _attr_icon = "mdi:weather-lightning-rainy"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, entry: JmaConfigEntry) -> None:
        super().__init__(entry.runtime_data.warning)
        self._class20 = entry.data[CONF_CLASS20]
        self._area_name = entry.data[CONF_AREA_NAME]
        self._attr_unique_id = f"{entry.entry_id}_warnings"
        self.entity_id = f"sensor.{DOMAIN}_{self._class20}_warnings"
        self._attr_device_info = jma_device_info(entry)

    def _data(self) -> dict:
        return (self.coordinator.data or {}).get(self._class20) or _EMPTY

    @property
    def native_value(self) -> int:
        return self._data()["count"]

    @property
    def extra_state_attributes(self) -> dict:
        d = self._data()
        return {
            "summary": d["summary"],
            "warnings": d["warnings"],
            "has_special_warning": d["has_special_warning"],
            "max_level": d["max_level"],
            "report_datetime": d["report_datetime"],
            "area_name": self._area_name,
        }

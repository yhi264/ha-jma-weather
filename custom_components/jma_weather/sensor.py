"""集約 sensor: 発表中の警報件数 + 詳細属性。"""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import JmaConfigEntry
from .const import CONF_AREA_NAME, CONF_CLASS20, DOMAIN


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
        area_name = entry.data[CONF_AREA_NAME]
        class20 = entry.data[CONF_CLASS20]
        self._attr_unique_id = f"{entry.entry_id}_warnings"
        self.entity_id = f"sensor.{DOMAIN}_{class20}_warnings"
        self._area_name = area_name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"JMA {area_name}",
            manufacturer="気象庁",
            model="気象警報・注意報",
        )

    @property
    def native_value(self) -> int:
        return self.coordinator.data["count"]

    @property
    def extra_state_attributes(self) -> dict:
        d = self.coordinator.data
        return {
            "area_name": self._area_name,
            "summary": d["summary"],
            "warnings": d["warnings"],
            "has_special_warning": d["has_special_warning"],
            "report_datetime": d["report_datetime"],
        }

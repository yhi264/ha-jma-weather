"""現象ごと binary_sensor（雷/大雨/…）。on = 該当現象が発表/継続中。"""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass, BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import JmaConfigEntry
from .const import CONF_AREA_NAME, CONF_CLASS20, DOMAIN, PHENOMENA

_LEVEL_RANK = {"特別警報": 3, "警報": 2, "注意報": 1}


async def async_setup_entry(
    hass: HomeAssistant, entry: JmaConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities(
        JmaPhenomenonBinarySensor(entry, p) for p in PHENOMENA
    )


class JmaPhenomenonBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """1 現象 = 1 binary_sensor。"""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.SAFETY

    def __init__(self, entry: JmaConfigEntry, phenomenon: dict) -> None:
        super().__init__(entry.runtime_data.warning)
        self._codes = set(phenomenon["codes"])
        group = phenomenon["group"]
        class20 = entry.data[CONF_CLASS20]
        self._attr_name = phenomenon["name"]
        self._attr_unique_id = f"{entry.entry_id}_{group}"
        # 明示 entity_id（ASCII・安定・automation 参照しやすい）
        self.entity_id = f"binary_sensor.{DOMAIN}_{class20}_{group}"
        self._attr_entity_registry_enabled_default = phenomenon["enabled_default"]
        area_name = entry.data[CONF_AREA_NAME]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"JMA {area_name}",
            manufacturer="気象庁",
            model="気象警報・注意報",
        )

    def _active(self) -> list[dict]:
        return [w for w in self.coordinator.data["warnings"] if w["code"] in self._codes]

    @property
    def is_on(self) -> bool:
        return bool(self._active())

    @property
    def extra_state_attributes(self) -> dict:
        active = self._active()
        if not active:
            return {"level": "なし", "status": "なし"}
        # 最上位レベルの警報を代表として属性に出す
        top = max(active, key=lambda w: _LEVEL_RANK.get(w["level"], 0))
        return {"level": top["level"], "status": top["status"]}

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

# 防災情報3種の定義: (group, 表示名, coordinator data キー)
_BOSAI_SENSORS = [
    ("doshakei", "土砂災害警戒情報", "doshakei"),
    ("tatsumaki", "竜巻注意情報", "tatsumaki"),
    ("kirokuame", "記録的短時間大雨情報", "kirokuame"),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: JmaConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    entities: list = [JmaPhenomenonBinarySensor(entry, p) for p in PHENOMENA]
    entities += [JmaBosaiBinarySensor(entry, *cfg) for cfg in _BOSAI_SENSORS]
    async_add_entities(entities)


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


class JmaBosaiBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """防災情報1種 = 1 binary_sensor（bosai coordinator 参照）。"""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.SAFETY

    def __init__(self, entry: JmaConfigEntry, group: str, name: str, key: str) -> None:
        super().__init__(entry.runtime_data.bosai)
        self._key = key
        class20 = entry.data[CONF_CLASS20]
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{group}"
        self.entity_id = f"binary_sensor.{DOMAIN}_{class20}_{group}"
        area_name = entry.data[CONF_AREA_NAME]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"JMA {area_name}",
            manufacturer="気象庁",
            model="気象警報・注意報",
        )

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data[self._key]["active"])

    @property
    def extra_state_attributes(self) -> dict:
        d = self.coordinator.data[self._key]
        attrs = {
            "info_type": d.get("info_type", ""),
            "report_datetime": d.get("report_datetime", ""),
            "headline": d.get("headline", ""),
        }
        if "valid_until" in d:
            attrs["valid_until"] = d["valid_until"]
        if "target_areas" in d:
            attrs["target_areas"] = d["target_areas"]
        return attrs

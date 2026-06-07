"""地点ごとの共通 DeviceInfo。"""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo

from . import JmaConfigEntry
from .const import CONF_AREA_NAME, DOMAIN


def jma_device_info(entry: JmaConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"JMA {entry.data[CONF_AREA_NAME]}",
        manufacturer="気象庁",
        model="気象警報・注意報",
    )

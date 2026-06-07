"""The JMA Weather integration."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_CLASS20, CONF_OFFICE, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL,
)
from .coordinator import JmaWarningCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


@dataclass
class JmaRuntimeData:
    """entry.runtime_data に格納する実行時オブジェクト。"""

    warning: JmaWarningCoordinator


type JmaConfigEntry = ConfigEntry[JmaRuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: JmaConfigEntry) -> bool:
    """config entry をセットアップする。"""
    session = async_get_clientsession(hass)
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    coordinator = JmaWarningCoordinator(
        hass,
        session=session,
        office_code=entry.data[CONF_OFFICE],
        class20_code=entry.data[CONF_CLASS20],
        scan_interval=scan_interval,
    )
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = JmaRuntimeData(warning=coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: JmaConfigEntry) -> bool:
    """config entry をアンロードする。"""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload(hass: HomeAssistant, entry: JmaConfigEntry) -> None:
    """options 変更時にリロード。"""
    await hass.config_entries.async_reload(entry.entry_id)

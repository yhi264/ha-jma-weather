"""The JMA Weather integration."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_CLASS20, CONF_OFFICE, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN,
)
from .coordinator import JmaBosaiFeedCoordinator, JmaWarningCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


@dataclass
class JmaRuntimeData:
    """entry.runtime_data に格納する実行時オブジェクト。"""

    warning: JmaWarningCoordinator
    bosai: JmaBosaiFeedCoordinator


type JmaConfigEntry = ConfigEntry[JmaRuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: JmaConfigEntry) -> bool:
    """config entry をセットアップする。"""
    session = async_get_clientsession(hass)
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    # 共有警報コーディネーター（HAに1つ）
    domain_data = hass.data.setdefault(DOMAIN, {})
    warning = domain_data.get("warning")
    if warning is None:
        warning = JmaWarningCoordinator(hass, session, scan_interval)
        domain_data["warning"] = warning
    warning.register_area(entry.data[CONF_CLASS20])
    await warning.async_refresh()

    # 防災(bosai)は地点ごと（office単位）
    bosai = JmaBosaiFeedCoordinator(
        hass,
        session=session,
        office_code=entry.data[CONF_OFFICE],
        class20_code=entry.data[CONF_CLASS20],
        scan_interval=scan_interval,
    )
    # bosai フィード(全国版・大)が一時的に落ちても 2a 警報センサーを巻き込まないよう、
    # ブロッキングしない async_refresh を使う（失敗時は bosai センサーが unavailable で自己回復）。
    await bosai.async_refresh()

    entry.runtime_data = JmaRuntimeData(warning=warning, bosai=bosai)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: JmaConfigEntry) -> bool:
    """config entry をアンロードする。"""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        warning = hass.data.get(DOMAIN, {}).get("warning")
        if warning is not None:
            warning.unregister_area(entry.data[CONF_CLASS20])
            if not warning.has_areas():
                hass.data[DOMAIN].pop("warning", None)
    return unloaded


async def _async_reload(hass: HomeAssistant, entry: JmaConfigEntry) -> None:
    """options 変更時にリロード。"""
    await hass.config_entries.async_reload(entry.entry_id)

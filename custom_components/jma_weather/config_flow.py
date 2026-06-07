"""Config flow for JMA Weather."""
from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .area import fetch_area, list_municipalities, list_offices, resolve_class10
from .const import (
    CONF_AREA_NAME, CONF_CLASS10, CONF_CLASS20, CONF_LATITUDE, CONF_LONGITUDE,
    CONF_OFFICE, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN,
)
from .coordinator import WARNING_URL


async def _test_warning(session: aiohttp.ClientSession, office_code: str) -> bool:
    """warning.json の到達性を検証。"""
    try:
        async with session.get(
            WARNING_URL.format(office=office_code),
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            resp.raise_for_status()
            await resp.json()
        return True
    except Exception:  # noqa: BLE001
        return False


class JmaConfigFlow(ConfigFlow, domain=DOMAIN):
    """JMA Weather の config flow。"""

    VERSION = 1

    def __init__(self) -> None:
        self._area: dict[str, Any] = {}
        self._office: str = ""
        self._class20: str = ""
        self._area_name: str = ""

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        session = async_get_clientsession(self.hass)
        try:
            self._area = await fetch_area(session)
        except Exception:  # noqa: BLE001
            return self.async_abort(reason="cannot_connect")
        return await self.async_step_office()

    async def async_step_office(self, user_input=None) -> ConfigFlowResult:
        if user_input is not None:
            self._office = user_input[CONF_OFFICE]
            return await self.async_step_municipality()
        offices = list_offices(self._area)
        return self.async_show_form(
            step_id="office",
            data_schema=vol.Schema(
                {vol.Required(CONF_OFFICE): vol.In({c: n for c, n in offices})}
            ),
        )

    async def async_step_municipality(self, user_input=None) -> ConfigFlowResult:
        if user_input is not None:
            self._class20 = user_input[CONF_CLASS20]
            munis = dict(list_municipalities(self._area, self._office))
            self._area_name = munis.get(self._class20, self._class20)
            await self.async_set_unique_id(self._class20)
            self._abort_if_unique_id_configured()
            session = async_get_clientsession(self.hass)
            if not await _test_warning(session, self._office):
                return self.async_abort(reason="cannot_connect")
            return await self.async_step_location()
        munis = list_municipalities(self._area, self._office)
        return self.async_show_form(
            step_id="municipality",
            data_schema=vol.Schema(
                {vol.Required(CONF_CLASS20): vol.In({c: n for c, n in munis})}
            ),
        )

    async def async_step_location(self, user_input=None) -> ConfigFlowResult:
        if user_input is not None:
            class10 = resolve_class10(self._area, self._class20)
            return self.async_create_entry(
                title=f"JMA {self._area_name}",
                data={
                    CONF_OFFICE: self._office,
                    CONF_CLASS20: self._class20,
                    CONF_CLASS10: class10,
                    CONF_AREA_NAME: self._area_name,
                    CONF_LATITUDE: user_input[CONF_LATITUDE],
                    CONF_LONGITUDE: user_input[CONF_LONGITUDE],
                },
            )
        return self.async_show_form(
            step_id="location",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_LATITUDE, default=self.hass.config.latitude): vol.All(
                        vol.Coerce(float), vol.Range(min=-90, max=90)
                    ),
                    vol.Required(CONF_LONGITUDE, default=self.hass.config.longitude): vol.All(
                        vol.Coerce(float), vol.Range(min=-180, max=180)
                    ),
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return JmaOptionsFlow()


class JmaOptionsFlow(OptionsFlow):
    """scan_interval を変更する options flow。"""

    async def async_step_init(self, user_input=None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        current = self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {vol.Required(CONF_SCAN_INTERVAL, default=current): vol.All(int, vol.Range(min=60))}
            ),
        )

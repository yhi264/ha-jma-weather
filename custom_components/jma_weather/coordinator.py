"""DataUpdateCoordinator for JMA warnings."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .jma_parse import parse_warnings

_LOGGER = logging.getLogger(__name__)

WARNING_URL = "https://www.jma.go.jp/bosai/warning/data/warning/{office}.json"


class JmaWarningCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """1 地点ぶんの警報を取得・パースする coordinator。"""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        office_code: str,
        class20_code: str,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{class20_code}",
            update_interval=timedelta(seconds=scan_interval),
        )
        self._session = session
        self._office_code = office_code  # 将来 office 共有 coordinator 化の布石
        self._class20_code = class20_code

    async def _async_update_data(self) -> dict[str, Any]:
        url = WARNING_URL.format(office=self._office_code)
        try:
            async with self._session.get(
                url, timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                resp.raise_for_status()
                payload = await resp.json()
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"JMA warning fetch failed: {err}") from err

        result = parse_warnings(payload, self._class20_code)
        if not result.get("area_found", True):
            _LOGGER.warning(
                "市町村コード %s が %s.json に見つかりません",
                self._class20_code, self._office_code,
            )
        return result

"""DataUpdateCoordinator for JMA warnings."""
from __future__ import annotations

import datetime as dt
import logging
from datetime import timedelta
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .bosai_feed import parse_feed, relevant_entries
from .bosai_parse import parse_doshakei, parse_kirokuame, parse_tatsumaki
from .const import (
    BOSAI_FEED_URL,
    DOMAIN,
    PRODUCT_DOSHA,
    PRODUCT_FUKEN,
    PRODUCT_SHUYAKU,
    PRODUCT_TATSUMAKI,
    WARNING_FEED_URL,
)
from .warning_r06 import parse_warnings_r06

_LOGGER = logging.getLogger(__name__)

class JmaWarningCoordinator(DataUpdateCoordinator[dict[str, dict]]):
    """HAに1つの共有コーディネーター。VPWS50(全国)を1回取得し登録class20のみパース。"""

    def __init__(self, hass: HomeAssistant, session, scan_interval: int) -> None:
        super().__init__(
            hass, _LOGGER, name=f"{DOMAIN}_warning",
            update_interval=timedelta(seconds=scan_interval),
        )
        self._session = session
        self._areas: set[str] = set()

    def register_area(self, class20_code: str) -> None:
        self._areas.add(class20_code)

    def unregister_area(self, class20_code: str) -> None:
        self._areas.discard(class20_code)

    def has_areas(self) -> bool:
        return bool(self._areas)

    async def _fetch_text(self, url: str) -> str:
        async with self._session.get(
            url, timeout=aiohttp.ClientTimeout(total=60)
        ) as resp:
            resp.raise_for_status()
            return await resp.text()

    async def _async_update_data(self) -> dict[str, dict]:
        try:
            feed = await self._fetch_text(WARNING_FEED_URL)
            entries = [e for e in parse_feed(feed) if e["product"] == PRODUCT_SHUYAKU]
            if not entries:
                raise UpdateFailed("VPWS50 not found in regular feed")
            latest = max(entries, key=lambda e: e["updated"])
            xml_text = await self._fetch_text(latest["url"])
        except UpdateFailed:
            raise
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"JMA warning(R06) fetch failed: {err}") from err
        return parse_warnings_r06(xml_text, set(self._areas))


class JmaBosaiFeedCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """防災情報XMLフィードから1地点ぶんの防災気象情報を取得する。"""

    def __init__(
        self,
        hass: HomeAssistant,
        session,
        office_code: str,
        class20_code: str,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_bosai_{class20_code}",
            update_interval=timedelta(seconds=scan_interval),
        )
        self._session = session
        self._office_code = office_code
        self._class20_code = class20_code

    def _now(self) -> dt.datetime:
        return dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))  # JST

    async def _fetch_text(self, url: str) -> str:
        async with self._session.get(
            url, timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            resp.raise_for_status()
            return await resp.text()

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            feed = await self._fetch_text(BOSAI_FEED_URL)
            entries = relevant_entries(parse_feed(feed), self._office_code)
            by_product = {e["product"]: e for e in entries}
            bodies: dict[str, str] = {}
            for prod, e in by_product.items():
                bodies[prod] = await self._fetch_text(e["url"])
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"JMA bosai fetch failed: {err}") from err

        now = self._now()
        empty = {"active": False, "info_type": "", "report_datetime": "", "headline": ""}

        if PRODUCT_DOSHA in bodies:
            doshakei = parse_doshakei(bodies[PRODUCT_DOSHA], self._class20_code)
        else:
            doshakei = {**empty, "target_areas": []}

        if PRODUCT_TATSUMAKI in bodies:
            tatsumaki = parse_tatsumaki(bodies[PRODUCT_TATSUMAKI], self._office_code, now)
        else:
            tatsumaki = {**empty, "valid_until": ""}

        if PRODUCT_FUKEN in bodies:
            kirokuame = parse_kirokuame(bodies[PRODUCT_FUKEN], now)
        else:
            kirokuame = dict(empty)

        return {"doshakei": doshakei, "tatsumaki": tatsumaki, "kirokuame": kirokuame}

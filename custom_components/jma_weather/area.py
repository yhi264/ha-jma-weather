"""area.json の取得と地域コード解決（HA 非依存の純ロジック + 取得関数）。"""
from __future__ import annotations

from typing import Any

import aiohttp

AREA_URL = "https://www.jma.go.jp/bosai/common/const/area.json"


async def fetch_area(session: aiohttp.ClientSession) -> dict[str, Any]:
    """area.json を取得して返す。"""
    async with session.get(AREA_URL, timeout=aiohttp.ClientTimeout(total=30)) as resp:
        resp.raise_for_status()
        return await resp.json()


def list_offices(area: dict[str, Any]) -> list[tuple[str, str]]:
    """(office_code, name) のリストを名称順で返す。"""
    offices = area.get("offices", {})
    return sorted(((code, o["name"]) for code, o in offices.items()), key=lambda x: x[1])


def list_municipalities(area: dict[str, Any], office_code: str) -> list[tuple[str, str]]:
    """指定 office 配下の (class20_code, name) を列挙する（office→class10→class15→class20）。"""
    result: list[tuple[str, str]] = []
    class10s = area.get("class10s", {})
    class15s = area.get("class15s", {})
    class20s = area.get("class20s", {})
    office = area.get("offices", {}).get(office_code, {})
    for c10 in office.get("children", []):
        for c15 in class10s.get(c10, {}).get("children", []):
            for c20 in class15s.get(c15, {}).get("children", []):
                name = class20s.get(c20, {}).get("name", c20)
                result.append((c20, name))
    return sorted(result, key=lambda x: x[1])


def resolve_class10(area: dict[str, Any], class20_code: str) -> str | None:
    """class20 から親チェーンを辿って class10 コードを返す。"""
    class20s = area.get("class20s", {})
    class15s = area.get("class15s", {})
    c20 = class20s.get(class20_code)
    if not c20:
        return None
    c15_code = c20.get("parent")
    c15 = class15s.get(c15_code)
    if not c15:
        return None
    return c15.get("parent")  # = class10 コード

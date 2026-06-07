"""防災情報XML Atom フィード(extra.xml)の解析（HA 非依存の純ロジック）。"""
from __future__ import annotations

import re
from typing import Any

from defusedxml import ElementTree as ET  # XXE/billion-laughs 対策。HA core 同梱

from .const import BOSAI_PRODUCTS

_ATOM = "{http://www.w3.org/2005/Atom}"
# ファイル名 {時刻}_0_{種別}_{office}.xml から種別と office を取る
_FNAME = re.compile(r"_0_([A-Z0-9]+)_(\d+)\.xml$")


def parse_feed(xml_text: str) -> list[dict[str, Any]]:
    """Atom フィード文字列を entry リストに変換する。"""
    root = ET.fromstring(xml_text)
    out: list[dict[str, Any]] = []
    for entry in root.findall(f"{_ATOM}entry"):
        url = (entry.findtext(f"{_ATOM}id") or "").strip()
        m = _FNAME.search(url)
        if not m:
            continue
        product, office = m.group(1), m.group(2)
        out.append(
            {
                "title": (entry.findtext(f"{_ATOM}title") or "").strip(),
                "url": url,
                "product": product,
                "office": office,
                "updated": (entry.findtext(f"{_ATOM}updated") or "").strip(),
                "content": (entry.findtext(f"{_ATOM}content") or "").strip(),
            }
        )
    return out


def relevant_entries(
    entries: list[dict[str, Any]], office_code: str
) -> list[dict[str, Any]]:
    """対象 office かつ対象種別の entry を、種別ごとに updated 最新1件だけ返す。"""
    latest: dict[str, dict[str, Any]] = {}
    for e in entries:
        if e["office"] != office_code or e["product"] not in BOSAI_PRODUCTS:
            continue
        cur = latest.get(e["product"])
        if cur is None or e["updated"] > cur["updated"]:
            latest[e["product"]] = e
    return list(latest.values())

"""気象警報・注意報（R06）集約通報(VPWS50)の解析（HA 非依存の純ロジック）。"""
from __future__ import annotations

import re
from typing import Any

from defusedxml import ElementTree as ET  # XXE/DoS 対策。HA core 非同梱のため依存に明示済

from .const import LEVEL_SPECIAL, code_info

# active とみなさない Status
_INACTIVE_STATUS = ("解除", "発表警報・注意報はなし", "")
# 全角数字→半角
_Z2H = str.maketrans("０１２３４５６７８９", "0123456789")
_LEVEL_RE = re.compile(r"^レベル([1-5])(.+)$")  # 警戒レベルは 1〜5


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def split_level(name: str) -> tuple[int | None, str]:
    """`レベルN種別` を (level:int, 種別名) に分解。レベル無しは (None, name)。全角数字対応。"""
    norm = name.translate(_Z2H)
    m = _LEVEL_RE.match(norm)
    if m:
        return int(m.group(1)), m.group(2)
    return None, name


def parse_warnings_r06(
    xml_text: str, class20_codes: set[str]
) -> dict[str, dict[str, Any]]:
    """VPWS50 XML から、指定 class20 群それぞれの警報結果を返す。

    返り値: { class20: {warnings:[{code,name,level,status}], count, summary,
              has_special_warning, max_level, report_datetime} }
    """
    root = ET.fromstring(xml_text)
    report_dt = ""
    for el in root.iter():
        if _local(el.tag) == "ReportDateTime" and el.text:
            report_dt = el.text.strip()
            break

    muni_warning = None
    for el in root.iter():
        if _local(el.tag) == "Warning" and el.get("type") == "気象警報・注意報（市町村等）":
            muni_warning = el
            break

    result: dict[str, dict[str, Any]] = {
        c: {"warnings": [], "count": 0, "summary": "なし",
            "has_special_warning": False, "max_level": None,
            "report_datetime": report_dt}
        for c in class20_codes
    }
    if muni_warning is None:
        return result

    for item in muni_warning:
        if _local(item.tag) != "Item":
            continue
        area_code = ""
        kinds: list[Any] = []
        for child in item:
            ln = _local(child.tag)
            if ln == "Area":
                for c in child:
                    if _local(c.tag) == "Code" and c.text:
                        area_code = c.text.strip()
            elif ln == "Kind":
                kinds.append(child)
        if area_code not in class20_codes:
            continue
        warnings: list[dict[str, Any]] = []
        for kind in kinds:
            name = code = status = ""
            for c in kind:
                ln = _local(c.tag)
                if ln == "Name" and c.text:
                    name = c.text.strip()
                elif ln == "Code" and c.text:
                    code = c.text.strip()
                elif ln == "Status" and c.text:
                    status = c.text.strip()
            if status in _INACTIVE_STATUS or not code:
                continue
            level, base = split_level(name)
            warnings.append({"code": code, "name": base, "level": level, "status": status})
        levels = [w["level"] for w in warnings if w["level"] is not None]
        result[area_code] = {
            "warnings": warnings,
            "count": len(warnings),
            "summary": "・".join(w["name"] for w in warnings) if warnings else "なし",
            "has_special_warning": any(
                code_info(w["code"])[1] == LEVEL_SPECIAL for w in warnings
            ),
            "max_level": max(levels) if levels else None,
            "report_datetime": report_dt,
        }
    return result

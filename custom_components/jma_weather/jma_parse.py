"""warning.json を正規化する純関数（HA 非依存）。"""
from __future__ import annotations

from typing import Any

from .const import LEVEL_SPECIAL, code_info

# active とみなす status（発表/継続）。解除・なしは active でない。
ACTIVE_STATUS = ("発表", "継続")


def _find_area(data: dict[str, Any], class20_code: str) -> dict | None:
    """areaTypes を走査し code 一致エリアを返す。"""
    for atype in data.get("areaTypes", []):
        for area in atype.get("areas", []):
            if area.get("code") == class20_code:
                return area
    return None


def parse_warnings(data: dict[str, Any], class20_code: str) -> dict[str, Any]:
    """warning.json と対象市町村コードから正規化データを返す。

    返り値:
      warnings: [{code,name,level,status}]  # active のみ
      count, summary, has_special_warning, report_datetime, area_found
    """
    report_dt = data.get("reportDatetime", "")
    area = _find_area(data, class20_code)
    if area is None:
        return {
            "warnings": [], "count": 0, "summary": "なし",
            "has_special_warning": False, "report_datetime": report_dt,
            "area_found": False,
        }

    warnings: list[dict[str, Any]] = []
    for w in area.get("warnings", []):
        code = w.get("code")
        status = w.get("status")
        # code 無し（=「発表警報・注意報はなし」プレースホルダ）は除外
        if not code:
            continue
        if status not in ACTIVE_STATUS:
            continue
        name, level, _group = code_info(str(code))
        warnings.append({"code": str(code), "name": name, "level": level, "status": status})

    has_special = any(w["level"] == LEVEL_SPECIAL for w in warnings)
    summary = "・".join(w["name"] for w in warnings) if warnings else "なし"
    return {
        "warnings": warnings,
        "count": len(warnings),
        "summary": summary,
        "has_special_warning": has_special,
        "report_datetime": report_dt,
        "area_found": True,
    }

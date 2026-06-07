import json
import pathlib

from custom_components.jma_weather.jma_parse import parse_warnings

FIX = pathlib.Path(__file__).parent / "fixtures"


def _load(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def test_none_is_empty():
    r = parse_warnings(_load("warning_none.json"), "4044700")
    assert r["warnings"] == []
    assert r["count"] == 0
    assert r["summary"] == "なし"
    assert r["has_special_warning"] is False
    assert r["report_datetime"] == "2026-05-28T11:31:00+09:00"


def test_multi_active_only():
    r = parse_warnings(_load("warning_multi.json"), "4044700")
    codes = {w["code"] for w in r["warnings"]}
    assert codes == {"14", "20"}
    assert r["count"] == 2
    assert "雷注意報" in r["summary"] and "濃霧注意報" in r["summary"]
    assert r["has_special_warning"] is False
    kaminari = next(w for w in r["warnings"] if w["code"] == "14")
    assert kaminari["name"] == "雷注意報"
    assert kaminari["level"] == "注意報"
    assert kaminari["status"] == "発表"


def test_special_detected_and_kaijo_excluded():
    r = parse_warnings(_load("warning_special.json"), "4044700")
    codes = {w["code"] for w in r["warnings"]}
    # 解除(code 10)は active でないので除外、33/04 のみ
    assert codes == {"33", "04"}
    assert r["has_special_warning"] is True


def test_area_not_found():
    r = parse_warnings(_load("warning_multi.json"), "9999999")
    assert r["warnings"] == []
    assert r["area_found"] is False

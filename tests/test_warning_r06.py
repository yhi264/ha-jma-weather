import pathlib

from custom_components.jma_weather.warning_r06 import parse_warnings_r06, split_level

FIX = pathlib.Path(__file__).parent / "fixtures"
XML = (FIX / "warning_shuyaku_min.xml").read_text(encoding="utf-8")


def test_split_level_fullwidth():
    assert split_level("レベル２大雨注意報") == (2, "大雨注意報")
    assert split_level("レベル５大雨特別警報") == (5, "大雨特別警報")
    assert split_level("波浪注意報") == (None, "波浪注意報")
    assert split_level("雷注意報") == (None, "雷注意報")


def test_parse_chikuzen_two_warnings_with_level():
    r = parse_warnings_r06(XML, {"4044700"})["4044700"]
    codes = {w["code"] for w in r["warnings"]}
    assert codes == {"10", "14"}
    ooame = next(w for w in r["warnings"] if w["code"] == "10")
    assert ooame["name"] == "大雨注意報"
    assert ooame["level"] == 2
    assert ooame["status"] == "継続"
    kaminari = next(w for w in r["warnings"] if w["code"] == "14")
    assert kaminari["level"] is None
    assert r["count"] == 2
    assert "大雨注意報" in r["summary"] and "雷注意報" in r["summary"]
    assert r["has_special_warning"] is False
    assert r["max_level"] == 2
    assert r["report_datetime"] == "2026-06-07T20:50:00+09:00"


def test_parse_beppu_wave():
    r = parse_warnings_r06(XML, {"4420200"})["4420200"]
    assert [w["code"] for w in r["warnings"]] == ["16"]
    assert r["warnings"][0]["name"] == "波浪注意報"


def test_parse_naha_none():
    r = parse_warnings_r06(XML, {"4720100"})["4720100"]
    assert r["warnings"] == []
    assert r["count"] == 0
    assert r["summary"] == "なし"


def test_parse_special_warning_and_maxlevel():
    r = parse_warnings_r06(XML, {"9999999"})["9999999"]
    assert r["has_special_warning"] is True
    assert r["max_level"] == 5


def test_parse_multiple_areas_at_once():
    res = parse_warnings_r06(XML, {"4044700", "4420200", "4720100"})
    assert set(res) == {"4044700", "4420200", "4720100"}
    assert res["4044700"]["count"] == 2
    assert res["4720100"]["count"] == 0

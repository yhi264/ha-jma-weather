import datetime as dt
import pathlib

from custom_components.jma_weather.bosai_parse import (
    parse_doshakei,
    parse_tatsumaki,
    parse_kirokuame,
)

FIX = pathlib.Path(__file__).parent / "fixtures"


def _load(name):
    return (FIX / name).read_text(encoding="utf-8")


def test_doshakei_active_for_target_class20():
    r = parse_doshakei(_load("doshakei_active.xml"), class20_code="4044700")
    assert r["active"] is True
    assert r["info_type"] == "発表"
    assert "筑前町" in r["target_areas"]


def test_doshakei_inactive_for_other_class20():
    r = parse_doshakei(_load("doshakei_active.xml"), class20_code="9999999")
    assert r["active"] is False


def test_doshakei_cleared_is_inactive():
    r = parse_doshakei(_load("doshakei_cleared.xml"), class20_code="4044700")
    assert r["active"] is False
    assert r["target_areas"] == []


def test_tatsumaki_active_when_valid_in_future():
    now = dt.datetime(2026, 6, 7, 13, 0, tzinfo=dt.timezone(dt.timedelta(hours=9)))
    r = parse_tatsumaki(_load("tatsumaki_active.xml"), office_code="400000", now=now)
    assert r["active"] is True
    assert r["valid_until"].startswith("2026-06-07T13:25")


def test_tatsumaki_inactive_when_valid_passed():
    now = dt.datetime(2026, 6, 7, 14, 0, tzinfo=dt.timezone(dt.timedelta(hours=9)))
    r = parse_tatsumaki(_load("tatsumaki_active.xml"), office_code="400000", now=now)
    assert r["active"] is False


def test_kirokuame_active_within_window():
    now = dt.datetime(2026, 6, 7, 12, 40, tzinfo=dt.timezone(dt.timedelta(hours=9)))
    r = parse_kirokuame(_load("fuken_kiroku.xml"), now=now)
    assert r["active"] is True
    assert "記録的短時間大雨" in r["headline"]


def test_kirokuame_inactive_for_normal_fuken():
    now = dt.datetime(2026, 6, 7, 12, 5, tzinfo=dt.timezone(dt.timedelta(hours=9)))
    r = parse_kirokuame(_load("fuken_normal.xml"), now=now)
    assert r["active"] is False


def test_kirokuame_inactive_after_window():
    now = dt.datetime(2026, 6, 7, 14, 0, tzinfo=dt.timezone(dt.timedelta(hours=9)))
    r = parse_kirokuame(_load("fuken_kiroku.xml"), now=now)
    assert r["active"] is False


def test_kirokuame_detected_by_head_title_only():
    # 見出し本文に語が無くても Head/Title に「記録的短時間大雨」があれば検出
    now = dt.datetime(2026, 6, 7, 12, 40, tzinfo=dt.timezone(dt.timedelta(hours=9)))
    r = parse_kirokuame(_load("fuken_kiroku_titleonly.xml"), now=now)
    assert r["active"] is True


def test_doshakei_real_data_only_warned_areas_active():
    # 実 VXWW50（沖縄）: 国頭村/東村 が「警戒」、那覇市等は「なし」
    body = _load("doshakei_real_okinawa.xml")
    assert parse_doshakei(body, "4730100")["active"] is True   # 国頭村（警戒）
    assert parse_doshakei(body, "4730300")["active"] is True   # 東村（警戒）
    assert parse_doshakei(body, "4720100")["active"] is False  # 那覇市（なし）
    # target_areas は警戒中のみ（県内全市町村ではない）
    r = parse_doshakei(body, "4730100")
    assert "国頭村" in r["target_areas"]
    assert "那覇市" not in r["target_areas"]

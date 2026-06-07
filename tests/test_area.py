import json
import pathlib

from custom_components.jma_weather.area import (
    list_offices,
    list_municipalities,
    resolve_class10,
)

FIX = pathlib.Path(__file__).parent / "fixtures"
AREA = json.loads((FIX / "area_min.json").read_text(encoding="utf-8"))


def test_list_offices():
    offices = list_offices(AREA)
    assert ("400000", "福岡県") in offices


def test_list_municipalities_under_office():
    munis = dict(list_municipalities(AREA, "400000"))
    assert munis["4044700"] == "筑前町"
    assert munis["4013000"] == "福岡市"


def test_resolve_class10_from_class20():
    # 筑前町(4044700) → class15(400041) → class10(400040 筑後地方)
    assert resolve_class10(AREA, "4044700") == "400040"
    assert resolve_class10(AREA, "4013000") == "400010"


def test_resolve_class10_unknown():
    assert resolve_class10(AREA, "9999999") is None

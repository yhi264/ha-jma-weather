from custom_components.jma_weather.const import (
    WARNING_CODES,
    PHENOMENA,
    LEVEL_SPECIAL,
    LEVEL_WARNING,
    LEVEL_ADVISORY,
    code_info,
)


def test_known_codes():
    assert WARNING_CODES["14"] == ("雷注意報", LEVEL_ADVISORY, "kaminari")
    assert WARNING_CODES["33"] == ("大雨特別警報", LEVEL_SPECIAL, "ooame")
    assert WARNING_CODES["03"][2] == "ooame"  # 大雨警報 も ooame グループ


def test_code_info_unknown():
    name, level, group = code_info("99")
    assert name == "不明な警報(99)"
    assert level == LEVEL_ADVISORY
    assert group == "unknown"


def test_phenomena_default_flags():
    kaminari = next(p for p in PHENOMENA if p["group"] == "kaminari")
    assert kaminari["enabled_default"] is True
    kansou = next(p for p in PHENOMENA if p["group"] == "kansou")
    assert kansou["enabled_default"] is False


def test_special_phenomenon_aggregates_special_codes():
    special = next(p for p in PHENOMENA if p["group"] == "tokubetsu")
    # 特別警報の現象は全特別警報コードを集約
    assert set(special["codes"]) == {"32", "33", "35", "36", "37", "38"}

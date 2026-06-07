"""Constants for the JMA Weather integration."""
from __future__ import annotations

DOMAIN = "jma_weather"

DEFAULT_SCAN_INTERVAL = 300  # 秒（警報）

# config entry / options キー
CONF_OFFICE = "office_code"
CONF_CLASS20 = "class20_code"
CONF_CLASS10 = "class10_code"
CONF_AREA_NAME = "area_name"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_SCAN_INTERVAL = "scan_interval"

# 区分（レベル）
LEVEL_SPECIAL = "特別警報"
LEVEL_WARNING = "警報"
LEVEL_ADVISORY = "注意報"

# JMA 警報コード → (名称, 区分, 現象グループ)
# 出典: 気象庁 防災情報XML/warning.json コード定義
WARNING_CODES: dict[str, tuple[str, str, str]] = {
    # 特別警報
    "32": ("暴風雪特別警報", LEVEL_SPECIAL, "boufuusetsu"),
    "33": ("大雨特別警報", LEVEL_SPECIAL, "ooame"),
    "35": ("暴風特別警報", LEVEL_SPECIAL, "boufuu"),
    "36": ("大雪特別警報", LEVEL_SPECIAL, "ooyuki"),
    "37": ("波浪特別警報", LEVEL_SPECIAL, "nami"),
    "38": ("高潮特別警報", LEVEL_SPECIAL, "takashio"),
    # 警報
    "02": ("暴風雪警報", LEVEL_WARNING, "boufuusetsu"),
    "03": ("大雨警報", LEVEL_WARNING, "ooame"),
    "04": ("洪水警報", LEVEL_WARNING, "kozui"),
    "05": ("暴風警報", LEVEL_WARNING, "boufuu"),
    "06": ("大雪警報", LEVEL_WARNING, "ooyuki"),
    "07": ("波浪警報", LEVEL_WARNING, "nami"),
    "08": ("高潮警報", LEVEL_WARNING, "takashio"),
    # 注意報
    "10": ("大雨注意報", LEVEL_ADVISORY, "ooame"),
    "12": ("大雪注意報", LEVEL_ADVISORY, "ooyuki"),
    "13": ("風雪注意報", LEVEL_ADVISORY, "fuusetsu"),
    "14": ("雷注意報", LEVEL_ADVISORY, "kaminari"),
    "15": ("強風注意報", LEVEL_ADVISORY, "kyoufuu"),
    "16": ("波浪注意報", LEVEL_ADVISORY, "nami"),
    "17": ("融雪注意報", LEVEL_ADVISORY, "yuusetsu"),
    "18": ("洪水注意報", LEVEL_ADVISORY, "kozui"),
    "19": ("高潮注意報", LEVEL_ADVISORY, "takashio"),
    "20": ("濃霧注意報", LEVEL_ADVISORY, "noumu"),
    "21": ("乾燥注意報", LEVEL_ADVISORY, "kansou"),
    "22": ("なだれ注意報", LEVEL_ADVISORY, "nadare"),
    "23": ("低温注意報", LEVEL_ADVISORY, "teion"),
    "24": ("霜注意報", LEVEL_ADVISORY, "shimo"),
    "25": ("着氷注意報", LEVEL_ADVISORY, "chakuhyou"),
    "26": ("着雪注意報", LEVEL_ADVISORY, "chakusetsu"),
}


def code_info(code: str) -> tuple[str, str, str]:
    """コードから (名称, 区分, 現象グループ) を返す。未知コードは安全側に処理。"""
    return WARNING_CODES.get(code, (f"不明な警報({code})", LEVEL_ADVISORY, "unknown"))


# 現象グループ（binary_sensor 1個 = 1現象）。codes はそのグループに属する全コード。
# tokubetsu は「特別警報が出ているか」を横断集約する特殊グループ。
PHENOMENA: list[dict] = [
    {"group": "kaminari", "name": "雷", "codes": ["14"], "enabled_default": True},
    {"group": "ooame", "name": "大雨", "codes": ["10", "03", "33"], "enabled_default": True},
    {"group": "kozui", "name": "洪水", "codes": ["18", "04"], "enabled_default": True},
    {"group": "boufuu", "name": "暴風", "codes": ["05", "35"], "enabled_default": True},
    {"group": "boufuusetsu", "name": "暴風雪", "codes": ["02", "32"], "enabled_default": True},
    {"group": "ooyuki", "name": "大雪", "codes": ["12", "06", "36"], "enabled_default": True},
    {"group": "nami", "name": "波浪", "codes": ["16", "07", "37"], "enabled_default": True},
    {"group": "takashio", "name": "高潮", "codes": ["19", "08", "38"], "enabled_default": True},
    {"group": "kyoufuu", "name": "強風", "codes": ["15"], "enabled_default": True},
    {"group": "noumu", "name": "濃霧", "codes": ["20"], "enabled_default": True},
    {"group": "tokubetsu", "name": "特別警報", "codes": ["32", "33", "35", "36", "37", "38"], "enabled_default": True},
    # 既定無効（雑然回避・必要なら options で有効化）
    {"group": "fuusetsu", "name": "風雪", "codes": ["13"], "enabled_default": False},
    {"group": "kansou", "name": "乾燥", "codes": ["21"], "enabled_default": False},
    {"group": "nadare", "name": "なだれ", "codes": ["22"], "enabled_default": False},
    {"group": "teion", "name": "低温", "codes": ["23"], "enabled_default": False},
    {"group": "shimo", "name": "霜", "codes": ["24"], "enabled_default": False},
    {"group": "chakuhyou", "name": "着氷", "codes": ["25"], "enabled_default": False},
    {"group": "chakusetsu", "name": "着雪", "codes": ["26"], "enabled_default": False},
    {"group": "yuusetsu", "name": "融雪", "codes": ["17"], "enabled_default": False},
]

# --- Phase 2b: 防災気象情報 ---
BOSAI_FEED_URL = "https://www.data.jma.go.jp/developer/xml/feed/extra.xml"

PRODUCT_DOSHA = "VXWW50"       # 土砂災害警戒情報
PRODUCT_TATSUMAKI = "VPHW50"   # 竜巻注意情報
PRODUCT_FUKEN = "VPFJ50"       # 府県気象情報（記録的短時間大雨情報を含む）
BOSAI_PRODUCTS = (PRODUCT_DOSHA, PRODUCT_TATSUMAKI, PRODUCT_FUKEN)

# 取消電文の無い瞬間情報の失効秒数
TATSUMAKI_FALLBACK_VALID_SEC = 3600  # ValidDateTime 欠落時のフォールバック
KIROKU_AME_VALID_SEC = 3600          # 記録的短時間大雨情報の自動失効

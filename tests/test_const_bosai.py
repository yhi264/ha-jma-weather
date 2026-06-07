from custom_components.jma_weather.const import (
    BOSAI_FEED_URL,
    PRODUCT_DOSHA,
    PRODUCT_TATSUMAKI,
    PRODUCT_FUKEN,
    TATSUMAKI_FALLBACK_VALID_SEC,
    KIROKU_AME_VALID_SEC,
    BOSAI_PRODUCTS,
)


def test_product_codes():
    assert PRODUCT_DOSHA == "VXWW50"
    assert PRODUCT_TATSUMAKI == "VPHW50"
    assert PRODUCT_FUKEN == "VPFJ50"


def test_feed_url():
    assert BOSAI_FEED_URL.endswith("/feed/extra.xml")


def test_valid_seconds():
    assert TATSUMAKI_FALLBACK_VALID_SEC == 3600
    assert KIROKU_AME_VALID_SEC == 3600


def test_bosai_products_set():
    assert set(BOSAI_PRODUCTS) == {"VXWW50", "VPHW50", "VPFJ50"}

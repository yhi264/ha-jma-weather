from custom_components.jma_weather.const import WARNING_FEED_URL, PRODUCT_SHUYAKU


def test_warning_feed_and_product():
    assert WARNING_FEED_URL.endswith("/feed/regular.xml")
    assert PRODUCT_SHUYAKU == "VPWS50"

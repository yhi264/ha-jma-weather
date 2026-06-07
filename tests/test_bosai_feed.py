import pathlib

from custom_components.jma_weather.bosai_feed import parse_feed, relevant_entries

FIX = pathlib.Path(__file__).parent / "fixtures"
FEED = (FIX / "extra_min.xml").read_text(encoding="utf-8")


def test_parse_feed_basic():
    entries = parse_feed(FEED)
    assert len(entries) == 4
    e = entries[0]
    assert e["product"] == "VXWW50"
    assert e["office"] == "400000"
    assert e["url"].endswith("_VXWW50_400000.xml")
    assert "筑前町" in e["content"]


def test_relevant_entries_filters_office_and_product():
    entries = parse_feed(FEED)
    rel = relevant_entries(entries, office_code="400000")
    products = {e["product"] for e in rel}
    assert products == {"VXWW50", "VPHW50", "VPFJ50"}
    assert all(e["office"] == "400000" for e in rel)


def test_relevant_entries_latest_per_product():
    entries = parse_feed(FEED)
    rel = relevant_entries(entries, office_code="400000")
    assert len(rel) == len({e["product"] for e in rel})

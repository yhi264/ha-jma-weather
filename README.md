# ha-jma-weather

**English** | [日本語](README.ja.md)

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A [Home Assistant](https://www.home-assistant.io/) custom integration that exposes **weather warnings, advisories, and emergency warnings** issued by the **Japan Meteorological Agency (JMA / 気象庁)** for any municipality in Japan.

It polls the official JMA open data (`warning/data/warning/{office}.json`) and creates, per location, an aggregate sensor (number of active warnings) plus one `binary_sensor` per phenomenon (thunderstorm, heavy rain, flood, …).

> **Status: Phase 2b (warnings/advisories + disaster-prevention info).** Weather forecast and precipitation nowcast are on the roadmap below.

## Features

- 🗾 Pick any municipality in Japan from a UI dropdown — no manual codes
- ⚡ One `binary_sensor` per phenomenon (`on` while issued/continuing) — easy automations
- 📊 Aggregate sensor with the full active-warning list in attributes
- 🚨 Emergency Warning (特別警報) detection
- 📍 Multiple locations (add the integration once per location)
- 🔁 Robust against JMA's "no warning" placeholder quirk; auto-recovers from fetch failures
- 🌐 No external dependencies; uses Home Assistant's built-in HTTP client

## Installation

### HACS (custom repository)

1. HACS → Integrations → ⋮ (top-right) → **Custom repositories**
2. Add `https://github.com/yhi264/ha-jma-weather` with category **Integration**
3. Install **JMA Weather**, then restart Home Assistant

> Once this repository is published to the HACS default store, the custom-repository step will no longer be necessary.

### Manual

Copy `custom_components/jma_weather/` into your Home Assistant `config/custom_components/` directory and restart.

## Configuration

Settings → Devices & Services → **Add Integration** → **JMA Weather**. The setup wizard fetches `area.json` and walks you through:

1. **Forecast region** (prefecture / 府県予報区) — dropdown
2. **Municipality** (市町村) — dropdown
3. **Coordinates** — defaults to your Home Assistant home location; editable (saved for the Phase 2d precipitation nowcast)

Options (changeable later): **update interval** in seconds (default `300` = 5 min, minimum `60`).

## Entities (one device per location)

### Aggregate sensor

- **`sensor.jma_weather_<class20>_warnings`** — number of active warnings/advisories (int)
  - Attributes: `summary` (e.g. `雷注意報・大雨警報` / `なし`), `warnings` (list of `{code, name, level, status}`), `has_special_warning`, `report_datetime`, `area_name`
  - Example: `sensor.jma_weather_4044700_warnings`

### Per-phenomenon binary sensors

- **`binary_sensor.jma_weather_<class20>_<group>`** — `on` while that phenomenon is **issued (発表) or continuing (継続)** (`device_class: safety`)
  - Attributes: `level` (Emergency Warning / Warning / Advisory), `status`. A single phenomenon spans advisory→warning→emergency levels; `level` reflects the highest active one.
  - Example: `binary_sensor.jma_weather_4044700_kaminari`

#### Phenomena (all enabled by default — disable any you don't need in the entity settings)

| group | Phenomenon | JMA codes |
|---|---|---|
| `kaminari` | Thunderstorm / 雷 | 14 |
| `ooame` | Heavy rain / 大雨 | 10 / 03 / 33 |
| `kozui` | Flood / 洪水 | 18 / 04 |
| `boufuu` | Gale / 暴風 | 05 / 35 |
| `boufuusetsu` | Snowstorm / 暴風雪 | 02 / 32 |
| `ooyuki` | Heavy snow / 大雪 | 12 / 06 / 36 |
| `nami` | High waves / 波浪 | 16 / 07 / 37 |
| `takashio` | Storm surge / 高潮 | 19 / 08 / 38 |
| `kyoufuu` | Strong wind / 強風 | 15 |
| `noumu` | Dense fog / 濃霧 | 20 |
| `tokubetsu` | Emergency Warning (any) / 特別警報 | 32 / 33 / 35 / 36 / 37 / 38 |
| `fuusetsu` | Snow & wind / 風雪 | 13 |
| `kansou` | Dry air / 乾燥 | 21 |
| `nadare` | Avalanche / なだれ | 22 |
| `teion` | Low temperature / 低温 | 23 |
| `shimo` | Frost / 霜 | 24 |
| `chakuhyou` | Icing / 着氷 | 25 |
| `chakusetsu` | Snow accretion / 着雪 | 26 |
| `yuusetsu` | Snowmelt / 融雪 | 17 |

#### Disaster-prevention info (Phase 2b, enabled by default)

| entity_id suffix | Information |
|---|---|
| `doshakei` | Landslide warning (土砂災害警戒情報) — municipality-level |
| `tatsumaki` | Tornado advisory (竜巻注意情報) — prefecture-level, ~1h validity |
| `kirokuame` | Record short-time heavy rain (記録的短時間大雨情報) — prefecture-level |

Attributes: `info_type`, `report_datetime`, `headline`, plus `valid_until` (tornado) and `target_areas` (landslide).

## Multiple locations

Add the integration once per location (1 config entry = 1 location). Locations in the same prefecture register as independent entries; entities and devices never collide (keyed by municipality code).

## Automation example

```yaml
automation:
  - alias: Notify on thunderstorm advisory
    trigger:
      - platform: state
        entity_id: binary_sensor.jma_weather_4044700_kaminari
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          message: "A thunderstorm advisory has been issued for your area."
```

## Data source & disclaimer

Data: Japan Meteorological Agency disaster-prevention information (`https://www.jma.go.jp/bosai/`). This project is not affiliated with or endorsed by the JMA.

## Roadmap

- **Phase 2c:** Weather forecast, temperature, precipitation probability → Home Assistant `weather` entity
- **Phase 2d:** Precipitation nowcast — "rain starts/stops in N minutes" (tile sampling)

## Development

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements-test.txt
./.venv/bin/pytest tests/ -q
```

Design documents live under `docs/superpowers/` (spec & implementation plan).

## License

MIT License © 2026 yhi264

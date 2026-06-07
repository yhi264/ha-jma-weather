# ha-jma-weather

[English](README.md) | **日本語**

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

気象庁（JMA）の防災情報から、日本国内の任意の市町村の**気象警報・注意報・特別警報**を取得する [Home Assistant](https://www.home-assistant.io/) カスタムインテグレーションです。

公式オープンデータ（`warning/data/warning/{office}.json`）をポーリングし、地点ごとに「発表中の件数」を表す集約センサーと、現象ごと（雷・大雨・洪水…）の `binary_sensor` を提供します。

> **ステータス：Phase 2a（警報・注意報）。** 天気予報・降水ナウキャストは下記ロードマップ参照。

## 特長

- 🗾 日本国内の市町村を UI のドロップダウンから選択（コード手入力不要）
- ⚡ 現象ごとに `binary_sensor`（発表中＝`on`）→ オートメーションが書きやすい
- 📊 集約センサーの属性に発表中警報の全リスト
- 🚨 特別警報の検出
- 📍 複数地点対応（地点ごとに統合を追加）
- 🔁 JMA の「警報なし」プレースホルダ仕様に頑健、取得失敗からは自動復帰
- 🌐 外部依存なし（HA 同梱の HTTP クライアントを使用）

## インストール

### HACS（カスタムリポジトリ）

1. HACS → 統合 → ⋮（右上）→ **カスタムリポジトリ**
2. `https://github.com/yhi264/ha-jma-weather` を種別 **Integration** で追加
3. **JMA Weather** をインストール → Home Assistant を再起動

> HACS デフォルトストアに公開された後は、カスタムリポジトリ追加の手順は不要になります。

### 手動

`custom_components/jma_weather/` を HA の `config/custom_components/` に配置して再起動。

## 設定（UI）

設定 → デバイスとサービス → **統合を追加** → **JMA Weather**。`area.json` を取得し、ウィザードで以下を選択します:

1. **府県予報区**（都道府県）をドロップダウンから選択
2. **市町村**を選択
3. **座標**を確認（既定は HA のホーム座標。任意の地点へ変更可。Phase 2d の降水ナウキャスト用に保存）

オプション（後から変更可）：**更新間隔（秒）**（既定 `300`＝5分、最小 `60`）。

## エンティティ（地点ごとに 1 デバイス）

### 集約センサー

- **`sensor.jma_weather_<class20>_warnings`** — 発表中の警報・注意報の**件数**（int）
  - 属性: `summary`（例「雷注意報・大雨警報」/「なし」）、`warnings`（`{code, name, level, status}` のリスト）、`has_special_warning`、`report_datetime`、`area_name`
  - 例: `sensor.jma_weather_4044700_warnings`

### 現象ごと binary_sensor

- **`binary_sensor.jma_weather_<class20>_<group>`** — その現象が**発表中または継続中**なら `on`（`device_class: safety`）
  - 属性: `level`（特別警報／警報／注意報）、`status`（発表／継続／なし）。1 現象が注意報〜特別警報の複数レベルを束ね、`level` に最上位を表示
  - 例: `binary_sensor.jma_weather_4044700_kaminari`

#### 既定で有効な現象（group）

| group | 現象 | JMA コード |
|---|---|---|
| `kaminari` | 雷 | 14 |
| `ooame` | 大雨 | 10 / 03 / 33 |
| `kozui` | 洪水 | 18 / 04 |
| `boufuu` | 暴風 | 05 / 35 |
| `boufuusetsu` | 暴風雪 | 02 / 32 |
| `ooyuki` | 大雪 | 12 / 06 / 36 |
| `nami` | 波浪 | 16 / 07 / 37 |
| `takashio` | 高潮 | 19 / 08 / 38 |
| `kyoufuu` | 強風 | 15 |
| `noumu` | 濃霧 | 20 |
| `tokubetsu` | 特別警報（いずれか）集約 | 32 / 33 / 35 / 36 / 37 / 38 |

#### 既定で無効な現象（必要なら HA のエンティティ設定で有効化）

`fuusetsu`（風雪）/ `kansou`（乾燥）/ `nadare`（なだれ）/ `teion`（低温）/ `shimo`（霜）/ `chakuhyou`（着氷）/ `chakusetsu`（着雪）/ `yuusetsu`（融雪）

## 複数地点

統合を地点ごとに複数追加します（1 エントリー = 1 地点）。同一府県内の別地点も独立エントリーとして登録でき、エンティティ・デバイスは衝突しません（市町村コードで一意化）。

## オートメーション例

```yaml
automation:
  - alias: 雷注意報が出たら通知
    trigger:
      - platform: state
        entity_id: binary_sensor.jma_weather_4044700_kaminari
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          message: "筑前町に雷注意報が発表されました"
```

## データ出典・免責

データ：気象庁 防災情報（`https://www.jma.go.jp/bosai/`）。本プロジェクトは気象庁が提供・公認するものではありません。

## ロードマップ

- **Phase 2b:** 防災気象情報（土砂災害警戒情報・記録的短時間大雨情報・竜巻注意情報）
- **Phase 2c:** 天気予報・気温・降水確率 → HA `weather` エンティティ
- **Phase 2d:** 降水ナウキャスト「あと○分で雨／止む」（タイルサンプリング）

## 開発

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements-test.txt
./.venv/bin/pytest tests/ -q
```

設計ドキュメントは `docs/superpowers/` 配下（spec / 実装計画）。

## ライセンス

MIT License © 2026 yhi264

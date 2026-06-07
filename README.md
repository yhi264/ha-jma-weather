# ha-jma-weather

気象庁（JMA）の防災情報から、指定地域の**気象警報・注意報・特別警報**を取得する Home Assistant カスタムインテグレーションです。

公式 JSON（`warning/data/warning/{office}.json`）をポーリングし、地点ごとに「発表中の件数」を表す集約センサーと、現象ごとの `binary_sensor` を提供します。

> ステータス: **Phase 2a（警報・注意報）**。天気予報・降水ナウキャストは下記ロードマップ参照。

## インストール

### HACS（カスタムリポジトリ）
1. HACS → 統合 → 右上メニュー → カスタムリポジトリ
2. リポジトリに `https://github.com/yhi264/ha-jma-weather`、種別「Integration」を追加
3. 「JMA Weather」をインストール → Home Assistant を再起動

### 手動
`custom_components/jma_weather/` を HA の `config/custom_components/` に配置して再起動。

## 設定（UI）

設定 → デバイスとサービス → 統合を追加 → 「JMA Weather」。`area.json` を取得し、以下をウィザードで選択します（手入力不要）:

1. **府県予報区**（都道府県／予報区）をドロップダウンから選択
2. **市町村**を選択
3. **座標**を確認（既定は HA のホーム座標。任意の地点へ変更可。Phase 2d の降水ナウキャスト用に保存）

オプション（後から変更可）: **更新間隔（秒）**（既定 300＝5分、最小 60）。

## エンティティ（地点ごとに 1 デバイス）

### 集約センサー
- **`sensor.jma_weather_<class20>_warnings`** — 発表中の警報・注意報の**件数**（int）
  - 属性: `summary`（例「雷注意報・大雨警報」/「なし」）、`warnings`（`{code,name,level,status}` のリスト）、`has_special_warning`、`report_datetime`、`area_name`
  - 例: `sensor.jma_weather_4044700_warnings`

### 現象ごと binary_sensor
- **`binary_sensor.jma_weather_<class20>_<group>`** — その現象が**発表中または継続中**なら `on`（`device_class: safety`）
  - 属性: `level`（特別警報／警報／注意報）、`status`（発表／継続／なし）。1 現象が注意報〜特別警報の複数レベルを束ね、`level` に最上位を表示
  - 例: `binary_sensor.jma_weather_4044700_kaminari`

#### 既定で有効な現象（group）
| group | 現象 | 含むコード |
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

## データ出典

気象庁 防災情報（`https://www.jma.go.jp/bosai/`）。本ソフトは気象庁の提供物ではありません。

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

# Phase 1 (REST+template) から jma_weather への移行

旧構成は REST センサー + template binary_sensor による雷注意報検知（`jma_thunder` ドメイン）。
新構成は `jma_weather` カスタムインテグレーションによる構造化取得。

## 移行手順

### 1. jma_weather 統合を追加

設定 → デバイスとサービス → 統合を追加 → 「JMA Weather」

- 地域名: `筑前町`
- 市町村コード: `4044700`
- 更新間隔: `300`（秒）

追加後、`binary_sensor.jma_weather_4044700_kaminari` が生成されることを確認する。
警報発表時は `on`、非発表時は `off` になることを確認（Developer Tools → States で確認可能）。

### 2. オートメーションの参照先を更新

既存オートメーション内の旧エンティティ参照を新エンティティに置き換える。

| 旧エンティティ | 新エンティティ |
|---|---|
| `binary_sensor.jma_thunder_active_chikuzen_hold` | `binary_sensor.jma_weather_4044700_kaminari` |
| `binary_sensor.jma_thunder_active_chikuzen` | `binary_sensor.jma_weather_4044700_kaminari` |
| `sensor.jma_warning_chikuzen_pretty` | `sensor.jma_weather_4044700_warnings` |

オートメーション YAML の `entity_id:` / `condition:` / `trigger:` を一括置換し、HA を再起動せずに「オートメーションを再読み込み」で反映できる。

### 3. 旧エンティティを削除

`configuration.yaml` から以下のブロックを削除し、HA を再起動する。

- `sensor:` の `rest` プラットフォーム（JMA 警報取得部分）
- `template:` の `binary_sensor`（`jma_thunder_active_*`）
- `input_boolean:` の hold フラグ（使用していた場合）
- 関連する `automation:` エントリー（hold 制御用オートメーション）

### 4. 動作確認

- `binary_sensor.jma_weather_4044700_kaminari` が `unavailable` にならないことを確認
- Developer Tools → Template で `{{ states('binary_sensor.jma_weather_4044700_kaminari') }}` が `on`/`off` を返すことを確認
- 旧エンティティが「見つからない」状態（unknown/unavailable）になっていることを確認し、削除する

## 旧構成との比較

| 項目 | 旧構成 (Phase 1) | 新構成 (jma_weather) |
|---|---|---|
| 取得方法 | REST sensor → template | DataUpdateCoordinator (aiohttp) |
| 255文字超リスク (case2) | あり（JSON 切り捨て → unavailable） | なし（構造化パース） |
| 対応現象 | 雷注意報のみ | 11 現象（特別警報含む） |
| 複数地点 | 手動 YAML 複製 | 統合を複数追加 |
| hold ロジック | input_boolean + automation | 不要（`継続` 状態を parse_warnings が処理） |

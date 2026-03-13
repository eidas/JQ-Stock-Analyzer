# J-Quants 株式分析ツール — システム仕様書

**プロジェクト名**: JQ Stock Analyzer  
**バージョン**: v0.1（初期設計）  
**最終更新**: 2026-03-13

---

## 1. プロジェクト概要

### 1.1 目的

J-Quants API（JPX公式）から取得した日本株データをローカルDBに蓄積し、ブラウザベースのGUIでスクリーニング・個別銘柄分析・ポートフォリオ管理・テクニカル分析・カスタム指標計算（回転日数インパクト分析等）を行う個人向け株式分析ツール。

### 1.2 想定ユーザー

個人投資家（1名）。ローカルPC上で起動し、ブラウザからアクセスする。マルチユーザー・認証機能は不要。

### 1.3 前提条件

- J-Quants API Lightプラン以上（月額¥1,650〜）を契約済み
- Python 3.10以上が動作するPC（Windows/Mac/Linux）
- ブラウザ（Chrome/Firefox/Edge）

---

## 2. 技術スタック

| レイヤー | 技術 | 選定理由 |
|:---|:---|:---|
| **バックエンド** | Python 3.10+ / FastAPI | J-Quants公式SDK（jquantsapi）がPython、非同期対応で高速 |
| **フロントエンド** | React 18 + TypeScript | SPA構成で複雑なUI（チャート・テーブル・フォーム）を管理しやすい |
| **UIフレームワーク** | Ant Design（antd） | テーブル・フォーム・チャート連携が充実、日本語対応 |
| **チャート** | Lightweight Charts（TradingView OSS） + Recharts | 株価チャート専用＋汎用グラフの二本立て |
| **データベース** | SQLite（WALモード） | ゼロ設定、単一ファイル、個人利用に最適 |
| **ORM** | SQLAlchemy 2.0 | Python標準のDB操作、マイグレーション対応 |
| **データ取得** | jquantsapi（公式SDK） | 認証・レート制限管理が内蔵済み |
| **データ加工** | pandas / NumPy | 指標計算・フィルタリングに不可欠 |
| **ビルド** | Vite | 高速HMR、Reactとの親和性 |

### 2.1 アーキテクチャ概要

```
┌──────────────────────────────────────────────────┐
│  ブラウザ（React SPA）                              │
│  localhost:5173                                   │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐    │
│  │スクリー │ │個別銘柄│ │ポートフ│ │カスタム│    │
│  │ニング  │ │分析    │ │ォリオ  │ │計算    │    │
│  └────┬───┘ └───┬────┘ └───┬────┘ └───┬────┘    │
│       └─────────┴──────────┴──────────┘          │
│                    REST API                       │
└────────────────────┬─────────────────────────────┘
                     │ HTTP (JSON)
┌────────────────────▼─────────────────────────────┐
│  FastAPI サーバー                                   │
│  localhost:8000                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │API Router│  │ビジネス   │  │計算エンジン│       │
│  │(REST)    │  │ロジック   │  │(pandas)   │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       └──────────────┴─────────────┘              │
│              │                │                    │
│       ┌──────▼──────┐  ┌─────▼──────┐            │
│       │  SQLite DB  │  │ J-Quants   │            │
│       │  (WAL)      │  │ API Client │            │
│       └─────────────┘  └────────────┘            │
└──────────────────────────────────────────────────┘
```

---

## 3. データベース設計

### 3.1 ER図（主要テーブル）

```
stocks (銘柄マスタ)
├── 1:N → daily_quotes (日次株価)
├── 1:N → financial_statements (財務サマリー)
├── 1:N → calculated_metrics (算出指標キャッシュ)
└── N:M → portfolio_items → portfolios (ポートフォリオ)
```

### 3.2 テーブル定義

#### stocks（銘柄マスタ）

| カラム | 型 | 説明 |
|:---|:---|:---|
| code | TEXT PK | 銘柄コード（例: "72030"） |
| name | TEXT NOT NULL | 銘柄名 |
| sector_17 | TEXT | 17業種区分 |
| sector_33 | TEXT | 33業種区分 |
| market_segment | TEXT | 市場区分（プライム等） |
| is_active | BOOLEAN | 上場中フラグ |
| updated_at | DATETIME | 最終更新日時 |

#### daily_quotes（日次株価・出来高）

| カラム | 型 | 説明 |
|:---|:---|:---|
| id | INTEGER PK | 自動連番 |
| code | TEXT FK → stocks | 銘柄コード |
| date | DATE NOT NULL | 取引日 |
| open | REAL | 始値（調整後） |
| high | REAL | 高値（調整後） |
| low | REAL | 安値（調整後） |
| close | REAL | 終値（調整後） |
| volume | INTEGER | 出来高（調整後） |
| turnover_value | REAL | 売買代金 |
| adjustment_factor | REAL | 調整係数 |
| **UNIQUE(code, date)** | | 複合ユニーク制約 |

**インデックス**: `idx_quotes_code_date (code, date DESC)`, `idx_quotes_date (date)`

#### financial_statements（財務サマリー）

| カラム | 型 | 説明 |
|:---|:---|:---|
| id | INTEGER PK | 自動連番 |
| code | TEXT FK → stocks | 銘柄コード |
| disclosed_date | DATE | 開示日 |
| fiscal_year | TEXT | 決算期（例: "2025-03"） |
| type_of_document | TEXT | 書類種別（1Q/2Q/3Q/本決算等） |
| net_sales | REAL | 売上高 |
| operating_profit | REAL | 営業利益 |
| ordinary_profit | REAL | 経常利益 |
| net_income | REAL | 純利益 |
| eps | REAL | EPS |
| bps | REAL | BPS |
| total_assets | REAL | 総資産 |
| equity | REAL | 自己資本 |
| equity_ratio | REAL | 自己資本比率 |
| shares_outstanding | INTEGER | 発行済株式数 |
| dividend_forecast | REAL | 配当予想（年間） |
| **UNIQUE(code, fiscal_year, type_of_document)** | | |

#### calculated_metrics（算出指標キャッシュ）

| カラム | 型 | 説明 |
|:---|:---|:---|
| id | INTEGER PK | 自動連番 |
| code | TEXT FK → stocks | 銘柄コード |
| date | DATE | 計算基準日 |
| per | REAL | PER（株価÷EPS） |
| pbr | REAL | PBR（株価÷BPS） |
| roe | REAL | ROE（純利益÷自己資本） |
| dividend_yield | REAL | 配当利回り |
| market_cap | REAL | 時価総額 |
| turnover_days | REAL | 回転日数（後述） |
| avg_volume_20d | REAL | 20日平均出来高 |
| avg_volume_60d | REAL | 60日平均出来高 |
| volatility_20d | REAL | 20日ヒストリカルVol |
| **UNIQUE(code, date)** | | |

#### portfolios（ポートフォリオ）

| カラム | 型 | 説明 |
|:---|:---|:---|
| id | INTEGER PK | 自動連番 |
| name | TEXT NOT NULL | ポートフォリオ名 |
| description | TEXT | メモ |
| created_at | DATETIME | 作成日時 |

#### portfolio_items（ポートフォリオ構成銘柄）

| カラム | 型 | 説明 |
|:---|:---|:---|
| id | INTEGER PK | 自動連番 |
| portfolio_id | INTEGER FK → portfolios | |
| code | TEXT FK → stocks | 銘柄コード |
| shares | INTEGER | 保有株数 |
| avg_cost | REAL | 平均取得単価 |
| acquired_date | DATE | 取得日 |
| memo | TEXT | メモ |

#### screening_presets（スクリーニング条件保存）

| カラム | 型 | 説明 |
|:---|:---|:---|
| id | INTEGER PK | 自動連番 |
| name | TEXT NOT NULL | プリセット名 |
| conditions_json | TEXT | 条件のJSON |
| created_at | DATETIME | 作成日時 |

#### data_sync_log（同期ログ）

| カラム | 型 | 説明 |
|:---|:---|:---|
| id | INTEGER PK | 自動連番 |
| sync_type | TEXT | 同期種別（quotes/statements/listings） |
| target_date | DATE | 対象日 |
| records_count | INTEGER | 取得件数 |
| status | TEXT | success / error |
| error_message | TEXT | エラー詳細 |
| started_at | DATETIME | 開始時刻 |
| completed_at | DATETIME | 完了時刻 |

---

## 4. 画面構成と機能仕様

### 4.0 共通レイアウト

```
┌──────────────────────────────────────────────┐
│  JQ Stock Analyzer     [データ同期] [設定]     │
├────────┬─────────────────────────────────────┤
│        │                                     │
│ サイド  │        メインコンテンツ               │
│ ナビ   │                                     │
│        │                                     │
│ 📊ダッシュ│                                   │
│ 🔍スクリ │                                    │
│ 📈個別  │                                     │
│ 💼ポート │                                    │
│ 🧮カスタム│                                   │
│ ⚙設定   │                                    │
│        │                                     │
├────────┴─────────────────────────────────────┤
│  同期状態: 最終更新 2026-03-13 20:00          │
└──────────────────────────────────────────────┘
```

---

### 4.1 ダッシュボード画面

**目的**: データの鮮度確認と主要指標の一覧

**構成要素**:
- データ同期ステータスカード（最終取得日時、各テーブルのレコード数）
- 市場概況サマリー（日経平均・TOPIX等の直近値 ※銘柄指定で表示）
- ポートフォリオ損益サマリー（設定済みポートフォリオの評価額推移ミニチャート）
- 直近のスクリーニング結果ショートカット

---

### 4.2 スクリーニング画面

**目的**: 複数条件で全銘柄をフィルタリングし、投資候補を抽出

#### 4.2.1 フィルタ条件ビルダー

条件を動的に追加・削除できるUIで、以下の指標に対応する。

**指標カテゴリと利用可能フィルタ**:

| カテゴリ | 指標 | 演算子 |
|:---|:---|:---|
| **株価** | 終値、前日比(%)、年初来騰落率 | >, <, 範囲 |
| **バリュエーション** | PER, PBR, 配当利回り | >, <, 範囲 |
| **収益性** | ROE, 営業利益率, 経常利益率 | >, <, 範囲 |
| **財務健全性** | 自己資本比率 | >, <, 範囲 |
| **規模** | 時価総額, 売上高 | >, <, 範囲 |
| **流動性** | 回転日数, 20日平均出来高, 売買代金 | >, <, 範囲 |
| **テクニカル** | 移動平均乖離率(5/25/75日), RSI(14) | >, <, 範囲 |
| **属性** | 市場区分, 業種(17/33), 銘柄名（部分一致） | 選択, 含む |

#### 4.2.2 条件の論理結合

- 条件間はデフォルトAND結合
- グループ化によるOR結合にも対応（条件グループ単位）
- 例: 「(PER < 15 AND PBR < 1) OR (配当利回り > 4%）」

#### 4.2.3 結果テーブル

| 機能 | 仕様 |
|:---|:---|
| 表示列 | 銘柄コード、銘柄名、市場、業種、終値、前日比、PER、PBR、ROE、配当利回り、回転日数、時価総額 |
| ソート | 任意列でクリックソート（昇順/降順） |
| ページング | 50件/ページ、ページ送り |
| 銘柄リンク | 銘柄コードクリックで個別銘柄画面へ遷移 |
| エクスポート | CSV/Excelダウンロード |
| プリセット保存 | 条件セットに名前を付けて保存・呼び出し |
| ポートフォリオ追加 | チェックボックスで複数選択 → ポートフォリオ一括追加 |

---

### 4.3 個別銘柄分析画面

**目的**: 1銘柄の詳細データを多角的に分析

#### 4.3.1 ヘッダー部

```
┌──────────────────────────────────────────────────┐
│ 7203 トヨタ自動車  プライム │ 輸送用機器              │
│ ¥2,845  +32 (+1.14%)  2026/03/13               │
│ [ポートフォリオに追加] [ウォッチリストに追加]        │
└──────────────────────────────────────────────────┘
```

#### 4.3.2 タブ構成

**① サマリータブ**
- 主要指標カード: PER / PBR / ROE / 配当利回り / 時価総額 / 自己資本比率
- 回転日数カード（20日/60日ベース）
- 52週高値・安値、年初来パフォーマンス
- 直近の決算サマリー（売上高・営業利益・純利益のYoY比較）

**② チャートタブ**（詳細は4.5節）
- 株価チャート（ローソク足）+ 出来高バー
- 期間選択: 1M / 3M / 6M / 1Y / 3Y / 5Y / 全期間
- テクニカル指標オーバーレイ（後述）

**③ 財務タブ**
- 四半期・通期の業績推移テーブル（横スクロール対応、最大20期分）
- 主要財務指標の棒グラフ/折れ線グラフ（売上高・営業利益・純利益の推移）
- EPS / BPS / 配当の推移グラフ
- 財務比率の推移（営業利益率・ROE・自己資本比率）

**④ 流動性・回転日数タブ**（詳細は4.6節）
- 回転日数の日次推移チャート
- 出来高分析（20/60日移動平均、出来高急増検知）
- インパクト分析シミュレーター

**⑤ 比較タブ**
- 最大5銘柄までの同業他社比較テーブル
- 比較チャート（株価の正規化重ね合わせ）

---

### 4.4 ポートフォリオ管理画面

**目的**: 保有銘柄の評価損益・資産配分を管理

#### 4.4.1 ポートフォリオ一覧

- 複数ポートフォリオ作成可能（「実際の保有」「ウォッチリスト」「仮想ポートフォリオ」等）
- 各ポートフォリオの合計評価額・損益率のカード表示

#### 4.4.2 ポートフォリオ詳細

**構成銘柄テーブル**:

| 列 | 内容 |
|:---|:---|
| 銘柄コード・名称 | リンク付き |
| 保有株数 | 入力値 |
| 平均取得単価 | 入力値 |
| 現在値 | DBから取得 |
| 評価額 | 自動計算 |
| 損益額 / 損益率 | 自動計算 |
| 配当利回り（取得価格ベース） | 自動計算 |
| 構成比率 | 評価額÷合計 |

**可視化**:
- セクター別構成比（ドーナツチャート）
- 評価額推移チャート（日次、折れ線）
- 損益ヒートマップ（銘柄×期間）

**操作**:
- 銘柄追加（検索ダイアログ）、編集、削除
- CSV一括インポート/エクスポート

---

### 4.5 チャート・テクニカル分析

#### 4.5.1 株価チャート仕様

**ライブラリ**: TradingView Lightweight Charts（Apache 2.0）

| 項目 | 仕様 |
|:---|:---|
| チャート種別 | ローソク足 / ライン / エリア（切替可能） |
| 出来高 | チャート下部にバー表示（陰陽色分け） |
| X軸 | 日付（営業日のみ、休日ギャップなし） |
| Y軸 | 自動スケール + 手動レンジ指定可能 |
| ズーム・スクロール | マウスホイール / ドラッグ |
| クロスヘア | マウス位置のOHLCV値をツールチップ表示 |

#### 4.5.2 テクニカル指標（オーバーレイ/サブチャート）

**第1弾で実装する指標**:

| 指標 | 種別 | デフォルトパラメータ |
|:---|:---|:---|
| 単純移動平均（SMA） | オーバーレイ | 5, 25, 75日 |
| 指数移動平均（EMA） | オーバーレイ | 12, 26日 |
| ボリンジャーバンド | オーバーレイ | 20日, ±2σ |
| 一目均衡表 | オーバーレイ | 9, 26, 52 |
| RSI | サブチャート | 14日 |
| MACD | サブチャート | 12, 26, 9 |
| 出来高移動平均 | 出来高オーバーレイ | 20日 |

**パラメータカスタマイズ**: 各指標の期間・パラメータをUIから変更可能

---

### 4.6 カスタム計算・回転日数インパクト分析

ここが本ツールの差別化ポイントとなる。

#### 4.6.1 回転日数の定義と計算

**回転日数 = 発行済株式数 ÷ N日平均出来高**

「全株式が一巡するのに何営業日かかるか」を示す流動性指標。値が小さいほど流動性が高い。

**計算パラメータ**:
- 平均出来高の算出期間: 20日 / 60日 / カスタム（UIで選択）
- 発行済株式数: financial_statementsの直近値を使用
- 浮動株ベースでの計算オプション（浮動株比率を手動入力可能にする）

#### 4.6.2 インパクト分析シミュレーター

「ある数量を売買した場合、市場に与えるインパクトはどの程度か」を推定する。

**入力パラメータ**:

| パラメータ | 説明 | デフォルト |
|:---|:---|:---|
| 売買数量（株数 or 金額） | シミュレーション対象 | — |
| 執行日数 | 何日に分けて執行するか | 1日 |
| 参加率上限 | 1日の出来高に対する売買量の割合上限 | 10% |
| 市場インパクトモデル | Square-root model 等 | Square-root |

**出力**:

| 出力項目 | 説明 |
|:---|:---|
| 推定インパクトコスト(%) | 価格変動の推定幅 |
| 推定執行日数 | 参加率上限を守る場合の最小日数 |
| 日別執行スケジュール | 各日の想定売買数量・参加率 |
| 出来高対比チャート | 売買量 vs 直近N日出来高の棒グラフ比較 |

**Square-root モデル（Almgren-Chriss簡易版）**:

```
Impact(%) = k × σ_daily × √(Q / V_avg)

k: インパクト係数（デフォルト 0.5、カスタマイズ可能）
σ_daily: 日次ボラティリティ（20日ヒストリカル）
Q: 売買数量
V_avg: N日平均出来高
```

#### 4.6.3 カスタム指標エンジン（将来拡張）

ユーザー定義の計算式で独自指標を作成する機能。初期バージョンでは以下をプリセット提供する。

| プリセット指標 | 計算式 | 用途 |
|:---|:---|:---|
| 回転日数（20日） | shares_outstanding / avg_vol_20d | 短期流動性 |
| 回転日数（60日） | shares_outstanding / avg_vol_60d | 中期流動性 |
| 出来高回転率 | avg_vol_20d / shares_outstanding | 回転日数の逆数（%表示） |
| 売買代金回転率 | avg_turnover_20d / market_cap | 資金の回転速度 |
| 流動性スコア | 0.4×(1/回転日数) + 0.3×売買代金_rank + 0.3×(1/bid-ask_rank) | 総合流動性評価 |
| インパクトスコア | impact(1億円) / σ_daily | 1億円売買時の標準化インパクト |

---

## 5. API設計（バックエンド REST API）

### 5.1 エンドポイント一覧

```
# データ同期
POST   /api/sync/quotes          # 日次株価の同期
POST   /api/sync/statements      # 財務データの同期
POST   /api/sync/listings        # 銘柄マスタの同期
POST   /api/sync/all             # 全データ一括同期
GET    /api/sync/status           # 同期状態取得

# スクリーニング
POST   /api/screening/search      # 条件検索実行
GET    /api/screening/presets      # プリセット一覧
POST   /api/screening/presets      # プリセット保存
DELETE /api/screening/presets/:id  # プリセット削除

# 個別銘柄
GET    /api/stocks/:code           # 銘柄サマリー
GET    /api/stocks/:code/quotes    # 株価履歴（期間指定）
GET    /api/stocks/:code/financials # 財務データ一覧
GET    /api/stocks/:code/metrics   # 算出指標一覧
GET    /api/stocks/:code/technicals # テクニカル指標計算結果
GET    /api/stocks/:code/impact    # インパクト分析

# ポートフォリオ
GET    /api/portfolios             # ポートフォリオ一覧
POST   /api/portfolios             # 新規作成
GET    /api/portfolios/:id         # 詳細取得
PUT    /api/portfolios/:id         # 更新
DELETE /api/portfolios/:id         # 削除
POST   /api/portfolios/:id/items   # 銘柄追加
PUT    /api/portfolios/:id/items/:item_id  # 銘柄編集
DELETE /api/portfolios/:id/items/:item_id  # 銘柄削除
GET    /api/portfolios/:id/performance     # パフォーマンス計算

# マスタ
GET    /api/master/sectors         # 業種一覧
GET    /api/master/markets         # 市場区分一覧
GET    /api/master/stocks/search   # 銘柄名インクリメンタルサーチ

# エクスポート
GET    /api/export/screening       # スクリーニング結果CSV
GET    /api/export/portfolio/:id   # ポートフォリオCSV
```

### 5.2 主要エンドポイント詳細

#### POST /api/screening/search

**リクエスト例**:
```json
{
  "conditions": [
    {
      "group": 1,
      "field": "per",
      "operator": "between",
      "value": [5, 15]
    },
    {
      "group": 1,
      "field": "pbr",
      "operator": "lt",
      "value": 1.0
    },
    {
      "group": 2,
      "field": "dividend_yield",
      "operator": "gt",
      "value": 4.0
    }
  ],
  "group_logic": "or",
  "sort_by": "per",
  "sort_order": "asc",
  "page": 1,
  "per_page": 50,
  "market_segments": ["プライム", "スタンダード"],
  "sectors_33": []
}
```

**レスポンス**:
```json
{
  "total": 142,
  "page": 1,
  "per_page": 50,
  "results": [
    {
      "code": "72030",
      "name": "トヨタ自動車",
      "market_segment": "プライム",
      "sector_33": "輸送用機器",
      "close": 2845.0,
      "change_pct": 1.14,
      "per": 9.8,
      "pbr": 0.95,
      "roe": 10.2,
      "dividend_yield": 3.1,
      "turnover_days_20": 45.2,
      "market_cap": 46500000000000,
      "date": "2026-03-13"
    }
  ]
}
```

#### GET /api/stocks/:code/impact

**クエリパラメータ**: `quantity=100000&days=5&participation_rate=0.1&vol_period=20`

**レスポンス**:
```json
{
  "code": "72030",
  "name": "トヨタ自動車",
  "input": {
    "quantity": 100000,
    "execution_days": 5,
    "max_participation_rate": 0.1
  },
  "market_data": {
    "avg_volume_20d": 15200000,
    "daily_volatility": 0.018,
    "close": 2845.0,
    "shares_outstanding": 16314987460
  },
  "result": {
    "estimated_impact_pct": 0.023,
    "estimated_impact_yen": 654,
    "min_execution_days": 1,
    "daily_schedule": [
      { "day": 1, "quantity": 100000, "participation_rate": 0.0066 }
    ]
  }
}
```

---

## 6. データ同期戦略

### 6.1 同期フロー

```
[ユーザー操作 or スケジューラ]
        │
        ▼
  ① 銘柄マスタ同期（/listings）
     全銘柄のコード・名称・業種・市場を取得
     → stocks テーブルを UPSERT
        │
        ▼
  ② 日次株価同期（/prices/daily_quotes）
     日付指定で全銘柄の株価を一括取得
     最終同期日+1 ～ 直近営業日 を日単位でループ
     → daily_quotes テーブルに INSERT（重複スキップ）
        │
        ▼
  ③ 財務データ同期（/fins/statements）
     日付指定で全銘柄の財務サマリーを取得
     → financial_statements テーブルに UPSERT
        │
        ▼
  ④ 算出指標の再計算
     直近のquotes + statementsから PER/PBR/ROE/回転日数等を計算
     → calculated_metrics テーブルに UPSERT
        │
        ▼
  ⑤ 同期ログ記録
     → data_sync_log に結果を INSERT
```

### 6.2 レートリミット対策

J-Quants API Lightプランのレートリミットは60件/分。

**日付指定API（`/prices/daily_quotes?date=YYYY-MM-DD`）を使えば、1リクエストで全銘柄（約3,800件）の当日株価を一括取得可能。** 従って株価同期は1営業日あたり1〜2リクエストで済む。

財務データも日付指定APIで同様に一括取得可能。月4回の同期であれば、1回あたり数十リクエストで完了し、レートリミットに到達するリスクは低い。

### 6.3 初回セットアップ（バルクインポート）

初回はLightプランの5年分データを全取得する必要がある。約1,250営業日 × 2リクエスト（株価+財務）= 約2,500リクエスト。60件/分で約42分で完了。バックグラウンドで実行し、進捗バーをUIに表示する。

---

## 7. 設定画面

| 設定項目 | 説明 | デフォルト |
|:---|:---|:---|
| J-Quants APIキー | 認証用（V2 APIキー方式） | — |
| 自動同期 | 起動時の自動データ同期ON/OFF | ON |
| 回転日数デフォルト期間 | スクリーニング等で使う標準期間 | 20日 |
| インパクト係数(k) | Square-rootモデルのk値 | 0.5 |
| 参加率上限デフォルト | インパクト分析のデフォルト参加率 | 10% |
| テーマ | ライト/ダーク | ダーク |
| DBファイルパス | SQLiteファイルの保存先 | ./data/jq_stock.db |

---

## 8. ディレクトリ構成

```
jq-stock-analyzer/
├── backend/
│   ├── main.py                  # FastAPIエントリポイント
│   ├── config.py                # 設定管理
│   ├── database.py              # SQLAlchemy設定
│   ├── models/                  # ORMモデル
│   │   ├── stock.py
│   │   ├── quote.py
│   │   ├── financial.py
│   │   ├── metric.py
│   │   ├── portfolio.py
│   │   └── sync_log.py
│   ├── routers/                 # APIルーター
│   │   ├── sync.py
│   │   ├── screening.py
│   │   ├── stocks.py
│   │   ├── portfolios.py
│   │   └── export.py
│   ├── services/                # ビジネスロジック
│   │   ├── jquants_client.py    # J-Quants API連携
│   │   ├── sync_service.py      # データ同期
│   │   ├── screening_service.py # スクリーニングエンジン
│   │   ├── metrics_service.py   # 指標計算エンジン
│   │   ├── impact_service.py    # インパクト分析
│   │   └── technical_service.py # テクニカル指標計算
│   ├── requirements.txt
│   └── alembic/                 # DBマイグレーション
│       └── versions/
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Screening.tsx
│   │   │   ├── StockDetail.tsx
│   │   │   ├── Portfolio.tsx
│   │   │   ├── CustomAnalysis.tsx
│   │   │   └── Settings.tsx
│   │   ├── components/
│   │   │   ├── charts/
│   │   │   │   ├── PriceChart.tsx
│   │   │   │   ├── VolumeChart.tsx
│   │   │   │   └── FinancialChart.tsx
│   │   │   ├── screening/
│   │   │   │   ├── ConditionBuilder.tsx
│   │   │   │   └── ResultTable.tsx
│   │   │   ├── portfolio/
│   │   │   │   ├── HoldingsTable.tsx
│   │   │   │   └── AllocationChart.tsx
│   │   │   ├── impact/
│   │   │   │   └── ImpactSimulator.tsx
│   │   │   └── common/
│   │   │       ├── StockSearch.tsx
│   │   │       └── SyncStatus.tsx
│   │   ├── hooks/
│   │   │   ├── useStockData.ts
│   │   │   └── useScreening.ts
│   │   ├── api/
│   │   │   └── client.ts        # Axios設定・API呼び出し
│   │   └── types/
│   │       └── index.ts         # TypeScript型定義
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── data/                        # SQLiteファイル格納
│   └── .gitkeep
├── scripts/
│   ├── init_db.py               # DB初期化
│   └── bulk_import.py           # 初回バルクインポート
├── docker-compose.yml           # (オプション)
├── README.md
└── .env                         # APIキー等
```

---

## 9. 開発フェーズ

### Phase 1: 基盤構築（1-2週間）

- [ ] プロジェクトセットアップ（FastAPI + React + SQLite）
- [ ] DBスキーマ作成・マイグレーション
- [ ] J-Quants API連携（認証・銘柄マスタ・株価・財務取得）
- [ ] データ同期サービス（手動トリガー）
- [ ] 算出指標計算エンジン（PER/PBR/ROE/配当利回り/回転日数）

### Phase 2: コア機能（2-3週間）

- [ ] スクリーニング画面（条件ビルダー + 結果テーブル）
- [ ] 個別銘柄サマリー画面
- [ ] 株価チャート（Lightweight Charts統合）
- [ ] テクニカル指標（SMA/EMA/ボリンジャー/RSI/MACD）

### Phase 3: 分析強化（2-3週間）

- [ ] インパクト分析シミュレーター
- [ ] 財務データ推移チャート
- [ ] ポートフォリオ管理（CRUD + 損益計算）
- [ ] ポートフォリオ可視化（構成比・推移）

### Phase 4: 仕上げ（1-2週間）

- [ ] ダッシュボード画面
- [ ] スクリーニングプリセット保存/呼出
- [ ] CSV/Excelエクスポート
- [ ] ダークテーマ対応
- [ ] エラーハンドリング・ログ整備
- [ ] README・セットアップガイド作成

---

## 10. 非機能要件

| 項目 | 要件 |
|:---|:---|
| **レスポンス** | スクリーニング実行: 3秒以内（キャッシュ済みデータ）、チャート描画: 1秒以内 |
| **データ容量** | 5年分全銘柄で約500MB〜1GB（SQLite） |
| **エラーハンドリング** | API障害時のリトライ（3回、指数バックオフ）、DB書込みエラーのロールバック |
| **ログ** | バックエンドはPython logging（INFO/WARNING/ERROR）、同期結果はDBに永続化 |
| **セキュリティ** | APIキーは.envファイルで管理、localhost限定アクセス（0.0.0.0バインド禁止） |
| **バックアップ** | SQLiteファイルの手動コピーで対応（日次バックアップスクリプト提供） |

---

## 11. 今後の拡張候補（スコープ外）

本仕様書の範囲外だが、将来的に検討する機能:

- **アラート機能**: 条件合致時のデスクトップ通知
- **バックテストエンジン**: 売買ルールの過去検証
- **ユーザー定義計算式エディタ**: GUIで自由に指標定義
- **yfinance併用モード**: J-Quants API非契約時のフォールバック
- **EDINET連携**: XBRL詳細財務データの自動取得・パース
- **LLM連携**: Claudeによる決算分析レポート自動生成
- **Premiumプラン対応**: 信用取引残高・空売りデータの分析

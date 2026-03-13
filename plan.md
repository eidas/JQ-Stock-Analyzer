# JQ Stock Analyzer — 実装計画書

**作成日**: 2026-03-13
**ベース仕様書**: spec.md v0.1

---

## 概要

本計画書は spec.md に定義されたシステム仕様を、具体的な実装タスクに分解したものである。
開発は4フェーズ構成とし、各フェーズ内のタスクは依存関係を考慮した順序で記載する。

---

## Phase 1: 基盤構築

データ取得・蓄積の基盤を構築するフェーズ。後続フェーズはすべてここで構築したデータ基盤に依存する。

### 1-1. プロジェクトセットアップ

**目的**: 開発環境の構築とディレクトリ構成の確立

**バックエンド**:
- [ ] `backend/` ディレクトリ作成
- [ ] `requirements.txt` 作成（fastapi, uvicorn, sqlalchemy, jquantsapi, pandas, numpy, alembic, python-dotenv）
- [ ] Python仮想環境セットアップ（venv）
- [ ] `backend/main.py` — FastAPIアプリケーションエントリポイント作成
  - CORSMiddleware設定（`http://localhost:5173` 許可）
  - ルーター登録の骨格
- [ ] `backend/config.py` — 設定管理（.envからの読み込み）
  - J-Quants APIキー、DBパス、各種デフォルト値
- [ ] `.env.example` 作成（APIキーのテンプレート）
- [ ] `.gitignore` 更新（venv, __pycache__, .env, data/*.db）

**フロントエンド**:
- [ ] `npm create vite@latest frontend -- --template react-ts` でプロジェクト生成
- [ ] 依存パッケージインストール
  - antd, @ant-design/icons
  - lightweight-charts, recharts
  - @tanstack/react-query
  - axios
  - react-router-dom
- [ ] `vite.config.ts` — プロキシ設定（`/api` → `http://localhost:8000`）
- [ ] `frontend/src/api/client.ts` — Axiosインスタンス設定（ベースURL、エラーハンドリング共通処理）
- [ ] `frontend/src/types/index.ts` — TypeScript型定義の骨格

**共通**:
- [ ] `data/` ディレクトリ + `.gitkeep`
- [ ] `scripts/` ディレクトリ

### 1-2. DBスキーマ作成・マイグレーション

**目的**: spec.md §3 のテーブル定義をSQLAlchemy ORMモデルとして実装

**タスク**:
- [ ] `backend/database.py` — SQLAlchemy エンジン・セッション設定
  - SQLite WALモード有効化
  - セッションファクトリ（`async_sessionmaker` or 同期セッション）
- [ ] ORMモデル作成（`backend/models/`）:
  - [ ] `stock.py` — stocks テーブル（PK: code TEXT 4桁）
  - [ ] `quote.py` — daily_quotes テーブル（UNIQUE(code, date)、インデックス定義）
  - [ ] `financial.py` — financial_statements テーブル（UNIQUE(code, fiscal_year, type_of_document)）
  - [ ] `metric.py` — calculated_metrics テーブル（UNIQUE(code, date)）
  - [ ] `portfolio.py` — portfolios + portfolio_items テーブル
  - [ ] `screening_preset.py` — screening_presets テーブル
  - [ ] `sync_log.py` — data_sync_log テーブル（progress_pct, current_step カラム含む）
- [ ] Alembic初期設定
  - `alembic init backend/alembic`
  - `alembic.ini` の `sqlalchemy.url` を設定
  - 初回マイグレーション生成・適用
- [ ] `scripts/init_db.py` — DB初期化スクリプト（テーブル作成確認用）

**注意点**:
- 銘柄コードは5桁→4桁変換を取得時に行う（モデル側は4桁TEXT前提）
- `shares_outstanding` は自己株式控除前の値であることをdocstringに記載

### 1-3. J-Quants API連携

**目的**: J-Quants公式SDKを使ったデータ取得クライアントの実装

**タスク**:
- [ ] `backend/services/jquants_client.py` 作成
  - jquantsapi SDKの初期化（APIキーによる認証）
  - 以下のラッパーメソッド実装:
    - `get_listed_stocks()` — 銘柄マスタ一覧取得
    - `get_daily_quotes(date: str)` — 日付指定での全銘柄株価取得
    - `get_financial_statements(date: str)` — 日付指定での財務データ取得
  - 5桁→4桁コード変換処理
  - エラーハンドリング（SDK例外のキャッチ、リトライ3回・指数バックオフ）
  - トークン期限切れ時のエラーメッセージ生成

**依存**: 1-1（config.pyのAPIキー設定）

### 1-4. データ同期サービス

**目的**: J-Quants APIからのデータ取得→DB格納の一連のパイプライン実装

**タスク**:
- [ ] `backend/services/sync_service.py` 作成
  - `sync_listings()` — 銘柄マスタ同期（stocks UPSERT）
  - `sync_quotes(from_date, to_date)` — 日次株価同期
    - 最終同期日+1 ～ 直近営業日をループ
    - daily_quotes へINSERT（重複スキップ: ON CONFLICT DO NOTHING）
    - 調整係数変更検知（adjustment_factor != 1.0）→ 過去データ再計算
  - `sync_statements(from_date, to_date)` — 財務データ同期（UPSERT）
  - `sync_all()` — 全データ一括同期（①listings → ②quotes → ③statements → ④metrics再計算）
  - 進捗更新: data_sync_logのprogress_pct, current_stepを逐次UPDATE
  - 排他制御: 同期処理の二重起動防止（ロックフラグ）
- [ ] `backend/routers/sync.py` 作成
  - `POST /api/sync/quotes` — 株価同期開始（202 Accepted + sync_id返却）
  - `POST /api/sync/statements` — 財務同期開始
  - `POST /api/sync/listings` — 銘柄マスタ同期開始
  - `POST /api/sync/all` — 全データ一括同期開始
  - `GET /api/sync/status` — 同期状態取得（進捗率・ステップ情報含む）
  - バックグラウンド実行: `asyncio.create_task()` で非同期処理
- [ ] 初回バルクインポート対応
  - `scripts/bulk_import.py` — コマンドラインからの初回データ投入
  - 約1,250営業日 × 株価＋財務 ≒ 2,500リクエスト（約42分）の進捗表示

**依存**: 1-2（DBモデル）、1-3（APIクライアント）

### 1-5. 算出指標計算エンジン

**目的**: 株価・財務データから投資指標を計算しキャッシュ

**タスク**:
- [ ] `backend/services/metrics_service.py` 作成
  - `calculate_metrics(code, date)` — 個別銘柄の指標計算
    - PER = 終値 ÷ EPS
    - PBR = 終値 ÷ BPS
    - ROE = 純利益 ÷ 自己資本
    - 配当利回り = 配当予想 ÷ 終値 × 100
    - 時価総額 = 終値 × 発行済株式数
    - 回転日数 = 発行済株式数 ÷ N日平均出来高
    - 20日/60日平均出来高
    - 20日ヒストリカルボラティリティ
  - `batch_calculate(date)` — 全銘柄一括計算（pandasベース高速処理）
  - calculated_metrics テーブルへのUPSERT
  - 財務データの最新レコード特定ロジック（直近のfiscal_yearから取得）

**依存**: 1-4（同期済みデータの存在が前提）

---

## Phase 2: コア機能

ユーザーが実際に操作するUI画面とバックエンドAPIの主要部分を実装するフェーズ。

### 2-1. フロントエンド共通レイアウト

**目的**: spec.md §4.0 の共通レイアウト（サイドナビ + ヘッダー + メインコンテンツ）を実装

**タスク**:
- [ ] `frontend/src/App.tsx` — React Router設定、共通レイアウト適用
  - サイドバー: Ant Design `Menu` + `Layout.Sider`
  - ヘッダー: データ同期ボタン、設定リンク
  - フッター: 最終同期日時表示
- [ ] `frontend/src/components/common/SyncStatus.tsx` — 同期状態表示コンポーネント
  - ヘッダーのミニ進捗インジケータ
  - 同期完了/エラー時のトースト通知（`notification`）
- [ ] ルーティング定義（6画面分のルート）
- [ ] ダークテーマの基本設定（Ant Design ConfigProvider）
- [ ] TanStack Query の Provider設定

### 2-2. スクリーニング機能（バックエンド）

**目的**: spec.md §4.2, §5.2 のスクリーニングAPI実装

**タスク**:
- [ ] `backend/services/screening_service.py` 作成
  - 条件パーサー: JSONリクエスト → SQLAlchemyクエリ変換
  - 対応フィールド: 終値, 前日比, PER, PBR, 配当利回り, ROE, 営業利益率, 経常利益率, 自己資本比率, 時価総額, 売上高, 回転日数, 平均出来高, 売買代金, 移動平均乖離率, RSI, 市場区分, 業種, 銘柄名
  - 対応演算子: gt, lt, between, eq, contains, in
  - グループ化: group番号でグルーピング、group_logicでAND/OR結合
  - ページネーション: page, per_page対応
  - ソート: sort_by, sort_order対応
  - `change_pct` のリアルタイム計算（直近2営業日の終値から）
- [ ] `backend/routers/screening.py` 作成
  - `POST /api/screening/search` — 条件検索実行
  - `GET /api/screening/presets` — プリセット一覧（Phase 4で詳細実装、骨格のみ）
  - `POST /api/screening/presets` — プリセット保存（同上）
  - `DELETE /api/screening/presets/:id` — プリセット削除（同上）
- [ ] テクニカル指標のリアルタイム計算（移動平均乖離率、RSI）をスクリーニング用に対応

**依存**: Phase 1（データ基盤・指標計算済み）

### 2-3. スクリーニング機能（フロントエンド）

**目的**: spec.md §4.2 のスクリーニングUIを実装

**タスク**:
- [ ] `frontend/src/pages/Screening.tsx` — スクリーニング画面メインコンポーネント
- [ ] `frontend/src/components/screening/ConditionBuilder.tsx` — 条件ビルダー
  - 条件の動的追加・削除UI
  - 指標カテゴリ選択 → フィールド選択 → 演算子 → 値入力
  - グループ化によるOR結合UI
  - Ant Design `Form`, `Select`, `InputNumber`, `Button` を活用
- [ ] `frontend/src/components/screening/ResultTable.tsx` — 結果テーブル
  - 表示列: コード, 銘柄名, 市場, 業種, 終値, 前日比, PER, PBR, ROE, 配当利回り, 回転日数, 時価総額
  - ソート: 列ヘッダークリック
  - ページネーション: 50件/ページ
  - 銘柄コードクリック → 個別銘柄画面遷移
- [ ] `frontend/src/hooks/useScreening.ts` — TanStack Query連携フック
- [ ] API型定義の追加（`types/index.ts`）

**依存**: 2-1（共通レイアウト）、2-2（スクリーニングAPI）

### 2-4. 個別銘柄サマリー画面

**目的**: spec.md §4.3 のヘッダー部とサマリータブを実装

**タスク**:
- [ ] `backend/routers/stocks.py` 作成
  - `GET /api/stocks/:code` — 銘柄サマリー（銘柄情報 + 直近株価 + 主要指標）
  - `GET /api/stocks/:code/quotes` — 株価履歴（from, toパラメータ対応）
  - `GET /api/stocks/:code/financials` — 財務データ一覧
  - `GET /api/stocks/:code/metrics` — 算出指標一覧
- [ ] `backend/routers/master.py` 作成
  - `GET /api/master/sectors` — 業種一覧
  - `GET /api/master/markets` — 市場区分一覧
  - `GET /api/master/stocks/search` — 銘柄インクリメンタルサーチ（query, limit）
- [ ] `frontend/src/pages/StockDetail.tsx` — 個別銘柄画面
  - ヘッダー部: コード、銘柄名、市場、業種、現在値、前日比
  - タブ構成: サマリー / チャート / 財務 / 流動性 / 比較
  - サマリータブ: 主要指標カード（PER, PBR, ROE, 配当利回り, 時価総額, 自己資本比率）
  - 回転日数カード（20日/60日ベース、発行済株式数の基準日併記）
  - 52週高値・安値、年初来パフォーマンス
  - 直近決算サマリー（売上高・営業利益・純利益 YoY比較）
- [ ] `frontend/src/components/common/StockSearch.tsx` — 銘柄検索ダイアログ
  - インクリメンタルサーチ（debounce 300ms）
  - Ant Design `AutoComplete`
- [ ] `frontend/src/hooks/useStockData.ts` — 銘柄データ取得フック

**依存**: 2-1（共通レイアウト）

### 2-5. 株価チャート

**目的**: spec.md §4.5 のチャート機能を実装

**タスク**:
- [ ] `frontend/src/components/charts/PriceChart.tsx` — 株価チャートコンポーネント
  - TradingView Lightweight Charts統合
  - チャート種別切替: ローソク足 / ライン / エリア
  - 出来高バー（チャート下部、陰陽色分け）
  - X軸: 営業日のみ（休日ギャップなし）
  - Y軸: 自動スケール
  - ズーム・スクロール（マウスホイール/ドラッグ）
  - クロスヘアツールチップ（OHLCV値表示）
  - 期間選択: 1M / 3M / 6M / 1Y / 3Y / 5Y / 全期間
- [ ] `frontend/src/components/charts/VolumeChart.tsx` — 出来高チャート（PriceChartに統合する形でも可）

**依存**: 2-4（個別銘柄画面のチャートタブに組み込み）

### 2-6. テクニカル指標

**目的**: spec.md §4.5.2 のテクニカル指標を実装

**タスク**:
- [ ] `backend/services/technical_service.py` 作成
  - SMA（5, 25, 75日）
  - EMA（12, 26日）
  - ボリンジャーバンド（20日, ±2σ）
  - 一目均衡表（9, 26, 52）— データ不足時はnull + warnings
  - RSI（14日）
  - MACD（12, 26, 9）
  - 出来高移動平均（20日）
  - パラメータカスタマイズ対応
  - pandas/NumPyによる計算
- [ ] `backend/routers/stocks.py` に追加
  - `GET /api/stocks/:code/technicals` — テクニカル指標計算結果
    - クエリパラメータ: from, to, indicators
    - データ不足時の warnings 配列返却
- [ ] フロントエンドのチャートにオーバーレイ/サブチャート描画
  - PriceChartへのSMA/EMA/ボリンジャー/一目均衡表のオーバーレイ追加
  - RSI/MACDのサブチャート追加
  - 指標ON/OFFトグル UI
  - パラメータ変更UI（Ant Design Drawer or Popover）

**依存**: 2-5（チャートコンポーネント）

---

## Phase 3: 分析強化

差別化機能（インパクト分析）とポートフォリオ管理を実装するフェーズ。

### 3-1. インパクト分析シミュレーター

**目的**: spec.md §4.6 のインパクト分析機能を実装

**タスク**:
- [ ] `backend/services/impact_service.py` 作成
  - Square-root モデル実装:
    ```
    Impact(%) = k × σ_daily × √(Q / V_avg)
    ```
  - 入力パラメータ処理:
    - 売買数量（株数 or 金額 → 金額の場合は終値で変換、単元株切り上げ）
    - 執行日数
    - 参加率上限
    - インパクト係数k（設定値からデフォルト取得）
  - 出力計算:
    - 推定インパクトコスト(%)
    - 推定インパクトコスト(円)
    - 推定執行日数（参加率上限ベース）
    - 日別執行スケジュール
  - 回転日数計算（20日/60日/カスタム）
  - 浮動株ベース計算オプション
- [ ] `backend/routers/stocks.py` に追加
  - `GET /api/stocks/:code/impact` — インパクト分析実行
- [ ] `frontend/src/components/impact/ImpactSimulator.tsx` 作成
  - 入力フォーム: 売買数量, 執行日数, 参加率上限, モデルパラメータ
  - 結果表示: インパクトコスト, 執行日数, 日別スケジュール
  - 出来高対比チャート（Recharts棒グラフ）
- [ ] 個別銘柄画面の「流動性・回転日数タブ」に統合
  - 回転日数の日次推移チャート
  - 出来高分析（20/60日移動平均、出来高急増検知）

**依存**: Phase 2（個別銘柄画面、チャート基盤）

### 3-2. 財務データ推移チャート

**目的**: spec.md §4.3.2 ③財務タブの可視化を実装

**タスク**:
- [ ] `frontend/src/components/charts/FinancialChart.tsx` 作成
  - 四半期・通期の業績推移テーブル（横スクロール、最大20期分）
  - Rechartsによるグラフ描画:
    - 売上高・営業利益・純利益の推移（棒グラフ + 折れ線）
    - EPS / BPS / 配当の推移グラフ
    - 財務比率推移（営業利益率, ROE, 自己資本比率）
- [ ] 個別銘柄画面の「財務タブ」に統合

**依存**: 2-4（個別銘柄画面）

### 3-3. ポートフォリオ管理（バックエンド）

**目的**: spec.md §4.4 のポートフォリオCRUD + 損益計算を実装

**タスク**:
- [ ] `backend/routers/portfolios.py` 作成
  - `GET /api/portfolios` — 一覧（各ポートフォリオの合計評価額・損益率含む）
  - `POST /api/portfolios` — 新規作成
  - `GET /api/portfolios/:id` — 詳細（構成銘柄 + 現在値 + 評価損益）
  - `PUT /api/portfolios/:id` — 更新
  - `DELETE /api/portfolios/:id` — 削除
  - `POST /api/portfolios/:id/items` — 銘柄追加
  - `PUT /api/portfolios/:id/items/:item_id` — 銘柄編集
  - `DELETE /api/portfolios/:id/items/:item_id` — 銘柄削除
  - `GET /api/portfolios/:id/performance` — パフォーマンス計算
- [ ] 損益計算ロジック
  - 評価額 = 現在値 × 保有株数
  - 損益額 = (現在値 - 平均取得単価) × 保有株数
  - 損益率 = (現在値 - 平均取得単価) / 平均取得単価 × 100
  - 配当利回り（取得価格ベース）= 配当予想 / 平均取得単価 × 100
  - 構成比率 = 評価額 / ポートフォリオ合計評価額

**依存**: Phase 1（DBモデル）

### 3-4. ポートフォリオ管理（フロントエンド）

**目的**: spec.md §4.4 のポートフォリオUIを実装

**タスク**:
- [ ] `frontend/src/pages/Portfolio.tsx` — ポートフォリオ画面
  - ポートフォリオ一覧: カード表示（名称, 評価額, 損益率）
  - ポートフォリオ新規作成・削除
- [ ] `frontend/src/components/portfolio/HoldingsTable.tsx` — 構成銘柄テーブル
  - 表示列: コード, 名称, 保有株数, 取得単価, 現在値, 評価額, 損益額, 損益率, 配当利回り, 構成比
  - 銘柄追加ダイアログ（StockSearch利用）
  - 編集・削除操作
- [ ] `frontend/src/components/portfolio/AllocationChart.tsx` — 可視化
  - セクター別構成比: ドーナツチャート（Recharts PieChart）
  - 評価額推移: 折れ線チャート
  - 損益ヒートマップ（銘柄×期間）
- [ ] CSV一括インポート/エクスポート機能

**依存**: 3-3（ポートフォリオAPI）

### 3-5. 比較タブ

**目的**: spec.md §4.3.2 ⑤比較タブの実装

**タスク**:
- [ ] 最大5銘柄の同業他社比較テーブル（主要指標の横並び比較）
- [ ] 比較チャート: 株価の正規化（基準日=100）重ね合わせ折れ線グラフ
- [ ] 銘柄追加UI（StockSearch利用、同一業種のサジェスト）

**依存**: 2-4（個別銘柄画面）、2-5（チャート基盤）

---

## Phase 4: 仕上げ

UX改善・エクスポート・テーマ対応などの仕上げフェーズ。

### 4-1. ダッシュボード画面

**目的**: spec.md §4.1 のダッシュボード実装

**タスク**:
- [ ] `frontend/src/pages/Dashboard.tsx`
  - データ同期ステータスカード（最終取得日時、テーブル別レコード数）
  - 市場概況サマリー（日経平均・TOPIX等、銘柄指定で表示）
  - ポートフォリオ損益サマリー（評価額推移ミニチャート）
  - 直近スクリーニング結果ショートカット

**依存**: Phase 2-3の主要機能

### 4-2. スクリーニングプリセット保存/呼出

**目的**: spec.md §4.2.3 のプリセット機能を完成

**タスク**:
- [ ] バックエンドのプリセットCRUDを完成（Phase 2で骨格作成済み）
- [ ] フロントエンドUI: プリセット名入力 → 保存、一覧から選択 → 条件復元
- [ ] スクリーニング画面へのポートフォリオ一括追加ボタン（チェックボックス選択）

### 4-3. CSV/Excelエクスポート

**目的**: spec.md §5.1 のエクスポートAPI実装

**タスク**:
- [ ] `backend/routers/export.py` 作成
  - `POST /api/export/screening` — スクリーニング結果CSV（全件出力、ページングなし）
  - `GET /api/export/portfolio/:id` — ポートフォリオCSV
  - Content-Type: text/csv, Content-Disposition: attachment
- [ ] フロントエンドのダウンロードボタン実装
  - スクリーニング結果テーブルのCSV/Excelボタン
  - ポートフォリオ画面のエクスポートボタン

### 4-4. ライトテーマ追加

**目的**: spec.md §7 のテーマ切替機能

**タスク**:
- [ ] Ant Design ConfigProviderのテーマトークン切替
- [ ] ダーク/ライト切替トグル（設定画面 + ヘッダー）
- [ ] Lightweight Chartsのテーマ連動（背景色、グリッド色、テキスト色）
- [ ] テーマ設定のlocalStorage永続化

### 4-5. 設定画面

**目的**: spec.md §7 の設定画面実装

**タスク**:
- [ ] `frontend/src/pages/Settings.tsx`
  - J-Quants APIキー入力（マスク表示、保存はバックエンドの.env更新 or DB保存）
  - 自動同期 ON/OFF
  - 回転日数デフォルト期間（20日/60日）
  - インパクト係数(k)
  - 参加率上限デフォルト
  - テーマ切替
  - DBファイルパス表示
- [ ] バックエンドの設定保存API（DB or ファイルベース）

### 4-6. エラーハンドリング・ログ整備

**目的**: spec.md §10 の非機能要件を満たす

**タスク**:
- [ ] バックエンド
  - Python logging設定（INFO/WARNING/ERROR）
  - グローバル例外ハンドラー（FastAPI exception_handler）
  - API障害時のリトライ（3回、指数バックオフ）— jquants_client.pyに実装済みの確認
  - DB書込みエラーのロールバック
  - トークン期限切れ時のユーザー向けエラーメッセージ
- [ ] フロントエンド
  - Axiosインターセプターでのエラー共通処理
  - Ant Design `message` / `notification` によるエラー表示
  - ネットワークエラー・タイムアウト時のリトライUI
  - ローディング状態の統一的な表示（Skeleton, Spin）

### 4-7. ドキュメント整備

**タスク**:
- [ ] README.md 更新
  - セットアップ手順（Python, Node.js, J-Quants APIキー取得）
  - 起動方法（バックエンド + フロントエンド）
  - 初回データ同期の手順
  - スクリーンショット
- [ ] 日次バックアップスクリプト作成（SQLiteファイルコピー）

---

## 技術的な注意事項

### パフォーマンス
- スクリーニング実行: 3秒以内（calculated_metricsのキャッシュ活用）
- チャート描画: 1秒以内
- SQLiteインデックスの適切な設定が鍵

### セキュリティ
- APIキーは`.env`で管理、Gitにコミットしない
- `uvicorn --host 127.0.0.1` でlocalhost限定
- `0.0.0.0` バインド禁止

### データ整合性
- 株価調整係数（stock split等）の遡及更新を同期時に処理
- `shares_outstanding` の基準日をUIに明示
- 一目均衡表は最低78営業日の過去データが必要（不足時はnull + warning）

### SQLite WALモード
- 同期処理中（書き込み）も読み取り操作は正常動作
- 同期処理の多重起動は禁止（ロックフラグで制御）

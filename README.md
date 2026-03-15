# JQ-Stock-Analyzer

J-Quants APIを利用して、日本株のスクリーニングや個別銘柄分析を行うローカルWebアプリです。

## 動作環境

- Python 3.10以上
- Node.js 20以上（npm含む）
- J-Quants APIのリフレッシュトークン
- （任意）[uv](https://docs.astral.sh/uv/) — pipの代替として使用可能

## インストール手順

### 1. リポジトリを準備

```powershell
git clone <このリポジトリのURL>
cd JQ-Stock-Analyzer
```

### 2. バックエンド依存関係をインストール

**pip/venv を使う場合:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

**uv を使う場合:**

```powershell
uv venv
uv pip install -r backend/requirements.txt
```

### 3. 環境変数ファイルを作成

プロジェクトルートに`.env`を作成し、以下を設定します。

```dotenv
JQUANTS_API_KEY=your_refresh_token_here
DB_PATH=data/jq_stock.db
AUTO_SYNC=true
```

補足:

- `JQUANTS_API_KEY` はJ-Quantsのリフレッシュトークンを設定してください。
- `DB_PATH` は未指定時でも `data/jq_stock.db` が使われます。

### 4. フロントエンド依存関係をインストール

```powershell
cd frontend
npm install
cd ..
```

### 5. データベースを初期化

**pip/venv を使う場合:**

```powershell
python scripts/init_db.py
```

**uv を使う場合:**

```powershell
uv run python scripts/init_db.py
```

## 起動手順

### 1. バックエンドを起動

**pip/venv を使う場合:**

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

**uv を使う場合:**

```powershell
uv run uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. フロントエンドを起動（別ターミナル）

```powershell
cd frontend
npm run dev
```

### 3. ブラウザでアクセス

- `http://localhost:5173`

## 初期データ取り込み（任意）

初回にまとめてデータを取り込みたい場合は、バックエンド起動前後で次を実行できます。

**pip/venv を使う場合:**

```powershell
python scripts/bulk_import.py
```

**uv を使う場合:**

```powershell
uv run python scripts/bulk_import.py
```

## よくある確認ポイント

- `J-Quants API key is not configured` が出る場合: `.env` の `JQUANTS_API_KEY` を確認
- フロントからAPIへ接続できない場合: バックエンドが `127.0.0.1:8000` で起動しているか確認
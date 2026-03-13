"""Application configuration loaded from environment variables."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# J-Quants API
JQUANTS_API_KEY: str = os.getenv("JQUANTS_API_KEY", "")

# Database
DB_PATH: str = os.getenv("DB_PATH", str(BASE_DIR / "data" / "jq_stock.db"))
DATABASE_URL: str = f"sqlite:///{DB_PATH}"

# Sync
AUTO_SYNC: bool = os.getenv("AUTO_SYNC", "true").lower() == "true"

# Defaults
TURNOVER_DAYS_DEFAULT_PERIOD: int = int(os.getenv("TURNOVER_DAYS_DEFAULT_PERIOD", "20"))
IMPACT_COEFFICIENT_K: float = float(os.getenv("IMPACT_COEFFICIENT_K", "0.5"))
PARTICIPATION_RATE_DEFAULT: float = float(os.getenv("PARTICIPATION_RATE_DEFAULT", "0.1"))

# Theme
THEME: str = os.getenv("THEME", "dark")

# CORS
ALLOWED_ORIGINS: list[str] = [
    "http://localhost:5173",
    "http://localhost:8000",
]

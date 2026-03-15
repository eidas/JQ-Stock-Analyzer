"""J-Quants API client wrapper using the official SDK (V2 API)."""

import logging
import time
from datetime import datetime, date
from typing import Any

import pandas as pd
from dateutil import tz

from backend.config import JQUANTS_API_KEY

logger = logging.getLogger(__name__)

JST = tz.gettz("Asia/Tokyo")


class JQuantsClient:
    """Wrapper around the jquantsapi SDK V2 with retry and rate-limit handling."""

    def __init__(self, api_key: str | None = None):
        import jquantsapi

        key = api_key or JQUANTS_API_KEY
        if not key:
            raise ValueError("J-Quants API key is not configured")
        self._client = jquantsapi.ClientV2(api_key=key)

    def _retry(self, func, *args, max_retries: int = 3, **kwargs) -> Any:
        """Execute with exponential backoff retry."""
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error("API call failed after %d retries: %s", max_retries, e)
                    raise
                wait = 2 ** attempt
                logger.warning("API call failed (attempt %d/%d), retrying in %ds: %s",
                               attempt + 1, max_retries, wait, e)
                time.sleep(wait)

    def get_listed_stocks(self) -> pd.DataFrame:
        """Fetch all listed stock information (V2: get_list)."""
        df = self._retry(self._client.get_list)
        if df is not None and not df.empty:
            # Convert 5-digit code to 4-digit
            if "Code" in df.columns:
                df["Code"] = df["Code"].astype(str).str[:4]
        return df

    def get_daily_quotes(self, date_str: str) -> pd.DataFrame:
        """Fetch daily quotes for a single date using V2 range API."""
        dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=JST)
        df = self._retry(
            self._client.get_eq_bars_daily_range,
            start_dt=dt,
            end_dt=dt,
        )
        if df is not None and not df.empty:
            if "Code" in df.columns:
                df["Code"] = df["Code"].astype(str).str[:4]
        time.sleep(1)
        return df

    def get_daily_quotes_range(self, from_date: date, to_date: date) -> pd.DataFrame:
        """Fetch daily quotes for a date range using V2 range API."""
        start_dt = datetime(from_date.year, from_date.month, from_date.day, tzinfo=JST)
        end_dt = datetime(to_date.year, to_date.month, to_date.day, tzinfo=JST)
        df = self._retry(
            self._client.get_eq_bars_daily_range,
            start_dt=start_dt,
            end_dt=end_dt,
        )
        if df is not None and not df.empty:
            if "Code" in df.columns:
                df["Code"] = df["Code"].astype(str).str[:4]
        return df

    def get_financial_statements(self, date_str: str) -> pd.DataFrame:
        """Fetch financial statements for a single date using V2 range API."""
        dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=JST)
        df = self._retry(
            self._client.get_fin_summary_range,
            start_dt=dt,
            end_dt=dt,
        )
        if df is not None and not df.empty:
            if "LocalCode" in df.columns:
                df["LocalCode"] = df["LocalCode"].astype(str).str[:4]
            elif "Code" in df.columns:
                df["Code"] = df["Code"].astype(str).str[:4]
        time.sleep(1)
        return df

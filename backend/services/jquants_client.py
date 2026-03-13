"""J-Quants API client wrapper using the official SDK."""

import logging
import time
from typing import Any

import pandas as pd

from backend.config import JQUANTS_API_KEY

logger = logging.getLogger(__name__)


class JQuantsClient:
    """Wrapper around the jquantsapi SDK with retry and rate-limit handling."""

    def __init__(self, api_key: str | None = None):
        import jquantsapi

        key = api_key or JQUANTS_API_KEY
        if not key:
            raise ValueError("J-Quants API key is not configured")
        self._client = jquantsapi.Client(mail_address="", password="", refresh_token=key)

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
        """Fetch all listed stock information."""
        df = self._retry(self._client.get_listed_info)
        if df is not None and not df.empty:
            # Convert 5-digit code to 4-digit
            if "Code" in df.columns:
                df["Code"] = df["Code"].astype(str).str[:4]
        return df

    def get_daily_quotes(self, date_str: str) -> pd.DataFrame:
        """Fetch daily quotes for all stocks on a given date (YYYY-MM-DD)."""
        date_yyyymmdd = date_str.replace("-", "")
        df = self._retry(self._client.get_prices_daily_quotes, date_yyyymmdd=date_yyyymmdd)
        if df is not None and not df.empty:
            if "Code" in df.columns:
                df["Code"] = df["Code"].astype(str).str[:4]
        # Rate-limit: small delay between consecutive API calls
        time.sleep(1)
        return df

    def get_financial_statements(self, date_str: str) -> pd.DataFrame:
        """Fetch financial statements disclosed on a given date."""
        date_yyyymmdd = date_str.replace("-", "")
        df = self._retry(
            self._client.get_fins_statements,
            date_yyyymmdd=date_yyyymmdd,
        )
        if df is not None and not df.empty:
            if "LocalCode" in df.columns:
                df["LocalCode"] = df["LocalCode"].astype(str).str[:4]
            elif "Code" in df.columns:
                df["Code"] = df["Code"].astype(str).str[:4]
        time.sleep(1)
        return df

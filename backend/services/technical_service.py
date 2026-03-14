"""Technical indicators calculation engine."""

import logging
from datetime import date

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import DailyQuote

logger = logging.getLogger(__name__)


def calculate_technicals(
    db: Session,
    code: str,
    from_date: date,
    to_date: date,
    indicators: list[str],
    params: dict | None = None,
) -> dict:
    """Calculate requested technical indicators for a stock."""
    params = params or {}

    # Fetch enough extra historical data for indicator warm-up (max 200 days extra)
    from datetime import timedelta
    extended_from = from_date - timedelta(days=300)

    rows = db.execute(
        select(DailyQuote).where(
            DailyQuote.code == code,
            DailyQuote.date >= extended_from,
            DailyQuote.date <= to_date,
        ).order_by(DailyQuote.date.asc())
    ).scalars().all()

    if not rows:
        return {"code": code, "period": {"from": from_date.isoformat(), "to": to_date.isoformat()}, "indicators": {}, "warnings": ["No data available"]}

    df = pd.DataFrame([{
        "date": r.date,
        "open": r.open,
        "high": r.high,
        "low": r.low,
        "close": r.close,
        "volume": r.volume,
    } for r in rows])
    df.set_index("date", inplace=True)
    df.sort_index(inplace=True)

    result = {}
    warnings = []

    for ind in indicators:
        if ind == "sma":
            result["sma"] = _calc_sma(df, from_date, params.get("sma_periods", [5, 25, 75]))
        elif ind == "ema":
            result["ema"] = _calc_ema(df, from_date, params.get("ema_periods", [12, 26]))
        elif ind == "bollinger":
            result["bollinger"] = _calc_bollinger(df, from_date,
                                                   params.get("bb_period", 20),
                                                   params.get("bb_std", 2))
        elif ind == "ichimoku":
            ich_result, ich_warn = _calc_ichimoku(df, from_date,
                                                    params.get("ich_tenkan", 9),
                                                    params.get("ich_kijun", 26),
                                                    params.get("ich_senkou_b", 52))
            result["ichimoku"] = ich_result
            warnings.extend(ich_warn)
        elif ind == "rsi":
            result["rsi"] = _calc_rsi(df, from_date, params.get("rsi_period", 14))
        elif ind == "macd":
            result["macd"] = _calc_macd(df, from_date,
                                         params.get("macd_fast", 12),
                                         params.get("macd_slow", 26),
                                         params.get("macd_signal", 9))
        elif ind == "volume_ma":
            result["volume_ma"] = _calc_volume_ma(df, from_date, params.get("vol_ma_period", 20))

    resp = {
        "code": code,
        "period": {"from": from_date.isoformat(), "to": to_date.isoformat()},
        "indicators": result,
    }
    if warnings:
        resp["warnings"] = warnings
    return resp


def _filter_range(df: pd.DataFrame, from_date: date) -> pd.DataFrame:
    return df[df.index >= from_date]


def _calc_sma(df: pd.DataFrame, from_date: date, periods: list[int]) -> dict:
    data = []
    for p in periods:
        df[f"sma_{p}"] = df["close"].rolling(window=p).mean()
    filtered = _filter_range(df, from_date)
    for idx, row in filtered.iterrows():
        entry = {"date": idx.isoformat() if hasattr(idx, 'isoformat') else str(idx)}
        for p in periods:
            val = row.get(f"sma_{p}")
            entry[f"sma_{p}"] = round(float(val), 2) if pd.notna(val) else None
        data.append(entry)
    return {"params": {"periods": periods}, "data": data}


def _calc_ema(df: pd.DataFrame, from_date: date, periods: list[int]) -> dict:
    data = []
    for p in periods:
        df[f"ema_{p}"] = df["close"].ewm(span=p, adjust=False).mean()
    filtered = _filter_range(df, from_date)
    for idx, row in filtered.iterrows():
        entry = {"date": idx.isoformat() if hasattr(idx, 'isoformat') else str(idx)}
        for p in periods:
            val = row.get(f"ema_{p}")
            entry[f"ema_{p}"] = round(float(val), 2) if pd.notna(val) else None
        data.append(entry)
    return {"params": {"periods": periods}, "data": data}


def _calc_bollinger(df: pd.DataFrame, from_date: date, period: int, std_dev: int) -> dict:
    df["bb_mid"] = df["close"].rolling(window=period).mean()
    df["bb_std"] = df["close"].rolling(window=period).std()
    df["bb_upper"] = df["bb_mid"] + std_dev * df["bb_std"]
    df["bb_lower"] = df["bb_mid"] - std_dev * df["bb_std"]

    filtered = _filter_range(df, from_date)
    data = []
    for idx, row in filtered.iterrows():
        data.append({
            "date": idx.isoformat() if hasattr(idx, 'isoformat') else str(idx),
            "upper": round(float(row["bb_upper"]), 2) if pd.notna(row["bb_upper"]) else None,
            "middle": round(float(row["bb_mid"]), 2) if pd.notna(row["bb_mid"]) else None,
            "lower": round(float(row["bb_lower"]), 2) if pd.notna(row["bb_lower"]) else None,
        })
    return {"params": {"period": period, "std_dev": std_dev}, "data": data}


def _calc_ichimoku(df: pd.DataFrame, from_date: date, tenkan: int, kijun: int, senkou_b: int):
    warnings = []
    min_required = senkou_b + kijun  # 78 days for default params
    if len(df) < min_required:
        warnings.append(f"ichimoku: insufficient data (need {min_required} days, have {len(df)})")

    high = df["high"]
    low = df["low"]
    close = df["close"]

    df["tenkan_sen"] = (high.rolling(tenkan).max() + low.rolling(tenkan).min()) / 2
    df["kijun_sen"] = (high.rolling(kijun).max() + low.rolling(kijun).min()) / 2
    df["senkou_span_a"] = ((df["tenkan_sen"] + df["kijun_sen"]) / 2).shift(kijun)
    df["senkou_span_b"] = ((high.rolling(senkou_b).max() + low.rolling(senkou_b).min()) / 2).shift(kijun)
    df["chikou_span"] = close.shift(-kijun)

    filtered = _filter_range(df, from_date)
    data = []
    for idx, row in filtered.iterrows():
        data.append({
            "date": idx.isoformat() if hasattr(idx, 'isoformat') else str(idx),
            "tenkan_sen": round(float(row["tenkan_sen"]), 2) if pd.notna(row.get("tenkan_sen")) else None,
            "kijun_sen": round(float(row["kijun_sen"]), 2) if pd.notna(row.get("kijun_sen")) else None,
            "senkou_span_a": round(float(row["senkou_span_a"]), 2) if pd.notna(row.get("senkou_span_a")) else None,
            "senkou_span_b": round(float(row["senkou_span_b"]), 2) if pd.notna(row.get("senkou_span_b")) else None,
            "chikou_span": round(float(row["chikou_span"]), 2) if pd.notna(row.get("chikou_span")) else None,
        })
    return {"params": {"tenkan": tenkan, "kijun": kijun, "senkou_span_b": senkou_b}, "data": data}, warnings


def _calc_rsi(df: pd.DataFrame, from_date: date, period: int) -> dict:
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    df["rsi"] = 100 - (100 / (1 + rs))

    filtered = _filter_range(df, from_date)
    data = []
    for idx, row in filtered.iterrows():
        val = row.get("rsi")
        data.append({
            "date": idx.isoformat() if hasattr(idx, 'isoformat') else str(idx),
            "value": round(float(val), 2) if pd.notna(val) else None,
        })
    return {"params": {"period": period}, "data": data}


def _calc_macd(df: pd.DataFrame, from_date: date, fast: int, slow: int, signal: int) -> dict:
    ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
    df["macd_line"] = ema_fast - ema_slow
    df["macd_signal"] = df["macd_line"].ewm(span=signal, adjust=False).mean()
    df["macd_hist"] = df["macd_line"] - df["macd_signal"]

    filtered = _filter_range(df, from_date)
    data = []
    for idx, row in filtered.iterrows():
        data.append({
            "date": idx.isoformat() if hasattr(idx, 'isoformat') else str(idx),
            "macd": round(float(row["macd_line"]), 2) if pd.notna(row.get("macd_line")) else None,
            "signal": round(float(row["macd_signal"]), 2) if pd.notna(row.get("macd_signal")) else None,
            "histogram": round(float(row["macd_hist"]), 2) if pd.notna(row.get("macd_hist")) else None,
        })
    return {"params": {"fast": fast, "slow": slow, "signal": signal}, "data": data}


def _calc_volume_ma(df: pd.DataFrame, from_date: date, period: int) -> dict:
    df["vol_ma"] = df["volume"].rolling(window=period).mean()
    filtered = _filter_range(df, from_date)
    data = []
    for idx, row in filtered.iterrows():
        val = row.get("vol_ma")
        data.append({
            "date": idx.isoformat() if hasattr(idx, 'isoformat') else str(idx),
            "value": round(float(val), 0) if pd.notna(val) else None,
        })
    return {"params": {"period": period}, "data": data}

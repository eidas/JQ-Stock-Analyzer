"""Metrics calculation engine — computes investment metrics from raw data."""

import logging
from datetime import date, timedelta

import numpy as np
import pandas as pd
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from backend.models import Stock, DailyQuote, FinancialStatement, CalculatedMetric

logger = logging.getLogger(__name__)


def calculate_metrics_for_stock(db: Session, code: str, calc_date: date) -> dict | None:
    """Calculate all metrics for a single stock on a given date."""
    # Get the latest close price
    quote = db.execute(
        select(DailyQuote).where(
            DailyQuote.code == code,
            DailyQuote.date <= calc_date,
        ).order_by(DailyQuote.date.desc()).limit(1)
    ).scalar_one_or_none()

    if not quote or not quote.close:
        return None

    close = quote.close

    # Get latest financial data
    fin = db.execute(
        select(FinancialStatement).where(
            FinancialStatement.code == code,
        ).order_by(FinancialStatement.disclosed_date.desc()).limit(1)
    ).scalar_one_or_none()

    # Compute valuation metrics
    per = close / fin.eps if fin and fin.eps and fin.eps != 0 else None
    pbr = close / fin.bps if fin and fin.bps and fin.bps != 0 else None
    roe = (fin.net_income / fin.equity * 100) if fin and fin.equity and fin.equity != 0 and fin.net_income else None
    div_yield = (fin.dividend_forecast / close * 100) if fin and fin.dividend_forecast and close > 0 else None
    shares = fin.shares_outstanding if fin else None
    market_cap = close * shares if shares else None
    operating_margin = (fin.operating_profit / fin.net_sales * 100) if fin and fin.net_sales and fin.net_sales != 0 and fin.operating_profit else None
    ordinary_margin = (fin.ordinary_profit / fin.net_sales * 100) if fin and fin.net_sales and fin.net_sales != 0 and fin.ordinary_profit else None

    # Compute volume metrics (20d and 60d averages)
    quotes_60d = db.execute(
        select(DailyQuote.volume, DailyQuote.close, DailyQuote.date).where(
            DailyQuote.code == code,
            DailyQuote.date <= calc_date,
        ).order_by(DailyQuote.date.desc()).limit(60)
    ).all()

    volumes = [q.volume for q in quotes_60d if q.volume is not None]
    closes = [q.close for q in quotes_60d if q.close is not None]

    avg_vol_20d = np.mean(volumes[:20]) if len(volumes) >= 20 else (np.mean(volumes) if volumes else None)
    avg_vol_60d = np.mean(volumes[:60]) if len(volumes) >= 60 else (np.mean(volumes) if volumes else None)

    turnover_days = shares / avg_vol_20d if shares and avg_vol_20d and avg_vol_20d > 0 else None

    # 20-day historical volatility
    vol_20d = None
    if len(closes) >= 21:
        recent_closes = list(reversed(closes[:21]))
        returns = np.diff(np.log(recent_closes))
        vol_20d = float(np.std(returns) * np.sqrt(252))

    # Year-to-date return
    ytd_return = None
    year_start = date(calc_date.year, 1, 1)
    first_quote = db.execute(
        select(DailyQuote.close).where(
            DailyQuote.code == code,
            DailyQuote.date >= year_start,
        ).order_by(DailyQuote.date.asc()).limit(1)
    ).scalar()
    if first_quote and first_quote > 0:
        ytd_return = (close - first_quote) / first_quote * 100

    return {
        "code": code,
        "date": calc_date,
        "per": per,
        "pbr": pbr,
        "roe": roe,
        "dividend_yield": div_yield,
        "market_cap": market_cap,
        "turnover_days": turnover_days,
        "avg_volume_20d": avg_vol_20d,
        "avg_volume_60d": avg_vol_60d,
        "volatility_20d": vol_20d,
        "operating_margin": operating_margin,
        "ordinary_margin": ordinary_margin,
        "ytd_return": ytd_return,
    }


def batch_calculate(db: Session, calc_date: date | None = None):
    """Calculate metrics for all active stocks."""
    if calc_date is None:
        # Use the latest date in daily_quotes
        latest = db.execute(select(func.max(DailyQuote.date))).scalar()
        calc_date = latest or date.today()

    stocks = db.execute(
        select(Stock.code).where(Stock.is_active == True)
    ).scalars().all()

    logger.info("Batch calculating metrics for %d stocks on %s", len(stocks), calc_date)

    for code in stocks:
        try:
            metrics = calculate_metrics_for_stock(db, code, calc_date)
            if not metrics:
                continue

            existing = db.execute(
                select(CalculatedMetric).where(
                    CalculatedMetric.code == code,
                    CalculatedMetric.date == calc_date,
                )
            ).scalar_one_or_none()

            if existing:
                for k, v in metrics.items():
                    if k not in ("code", "date"):
                        setattr(existing, k, v)
            else:
                db.add(CalculatedMetric(**metrics))

        except Exception as e:
            logger.error("Error calculating metrics for %s: %s", code, e)

    db.commit()
    logger.info("Batch calculation completed")

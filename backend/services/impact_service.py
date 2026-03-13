"""Impact analysis simulator — Square-root model (Almgren-Chriss simplified)."""

import math
import logging
from datetime import date

import numpy as np
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from backend.models import DailyQuote, FinancialStatement, CalculatedMetric
from backend.config import IMPACT_COEFFICIENT_K, PARTICIPATION_RATE_DEFAULT

logger = logging.getLogger(__name__)


def calculate_impact(
    db: Session,
    code: str,
    quantity: int,
    execution_days: int = 1,
    max_participation_rate: float | None = None,
    vol_period: int = 20,
    impact_k: float | None = None,
    float_ratio: float = 1.0,
) -> dict:
    """
    Calculate market impact using Square-root model.

    Impact(%) = k * sigma_daily * sqrt(Q / V_avg)

    Args:
        code: Stock code
        quantity: Number of shares to trade
        execution_days: Days to execute over
        max_participation_rate: Max % of daily volume (default from config)
        vol_period: Period for average volume calculation
        impact_k: Impact coefficient (default from config)
        float_ratio: Float ratio for adjusting shares outstanding (1.0 = 100%)
    """
    if max_participation_rate is None:
        max_participation_rate = PARTICIPATION_RATE_DEFAULT
    if impact_k is None:
        impact_k = IMPACT_COEFFICIENT_K

    # Get latest quote
    latest_quote = db.execute(
        select(DailyQuote).where(DailyQuote.code == code)
        .order_by(DailyQuote.date.desc()).limit(1)
    ).scalar_one_or_none()

    if not latest_quote or not latest_quote.close:
        return {"error": "No quote data available"}

    close = latest_quote.close

    # Get average volume
    volumes = db.execute(
        select(DailyQuote.volume).where(
            DailyQuote.code == code,
            DailyQuote.volume.isnot(None),
        ).order_by(DailyQuote.date.desc()).limit(vol_period)
    ).scalars().all()

    if not volumes:
        return {"error": "No volume data available"}

    avg_volume = float(np.mean(volumes))

    # Get daily volatility (20-day)
    closes = db.execute(
        select(DailyQuote.close).where(
            DailyQuote.code == code,
            DailyQuote.close.isnot(None),
        ).order_by(DailyQuote.date.desc()).limit(21)
    ).scalars().all()

    if len(closes) < 2:
        return {"error": "Insufficient data for volatility calculation"}

    recent_closes = list(reversed(closes))
    returns = np.diff(np.log(recent_closes))
    daily_volatility = float(np.std(returns))

    # Get shares outstanding
    fin = db.execute(
        select(FinancialStatement).where(FinancialStatement.code == code)
        .order_by(FinancialStatement.disclosed_date.desc()).limit(1)
    ).scalar_one_or_none()

    shares_outstanding = fin.shares_outstanding if fin and fin.shares_outstanding else None

    # Calculate per-day quantity if multi-day execution
    daily_quantity = quantity / execution_days

    # Check participation rate constraint
    min_execution_days = max(1, math.ceil(quantity / (avg_volume * max_participation_rate)))

    # Impact calculation: Impact(%) = k * sigma * sqrt(Q / V_avg)
    q_per_day = quantity / max(execution_days, min_execution_days)
    impact_pct = impact_k * daily_volatility * math.sqrt(q_per_day / avg_volume) * 100
    impact_yen = close * impact_pct / 100

    # Daily execution schedule
    actual_days = max(execution_days, min_execution_days)
    daily_schedule = []
    remaining = quantity
    for day in range(1, actual_days + 1):
        day_qty = min(remaining, int(avg_volume * max_participation_rate))
        if day == actual_days:
            day_qty = remaining
        participation = day_qty / avg_volume if avg_volume > 0 else 0
        daily_schedule.append({
            "day": day,
            "quantity": day_qty,
            "participation_rate": round(participation, 4),
        })
        remaining -= day_qty
        if remaining <= 0:
            break

    return {
        "code": code,
        "name": "",  # Populated by router
        "input": {
            "quantity": quantity,
            "execution_days": execution_days,
            "max_participation_rate": max_participation_rate,
        },
        "market_data": {
            f"avg_volume_{vol_period}d": avg_volume,
            "daily_volatility": round(daily_volatility, 6),
            "close": close,
            "shares_outstanding": shares_outstanding,
        },
        "result": {
            "estimated_impact_pct": round(impact_pct, 4),
            "estimated_impact_yen": round(impact_yen, 2),
            "min_execution_days": min_execution_days,
            "daily_schedule": daily_schedule,
        },
    }

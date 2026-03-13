"""Individual stock API endpoints."""

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Stock, DailyQuote, FinancialStatement, CalculatedMetric
from backend.services.technical_service import calculate_technicals
from backend.services.impact_service import calculate_impact

router = APIRouter()


@router.get("/{code}")
def get_stock_summary(code: str, db: Session = Depends(get_db)):
    """Get stock summary with latest quote and metrics."""
    stock = db.get(Stock, code)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    # Latest quote
    quote = db.execute(
        select(DailyQuote).where(DailyQuote.code == code)
        .order_by(DailyQuote.date.desc()).limit(1)
    ).scalar_one_or_none()

    # Previous quote for change_pct
    prev_quote = db.execute(
        select(DailyQuote).where(
            DailyQuote.code == code,
            DailyQuote.date < quote.date if quote else None,
        ).order_by(DailyQuote.date.desc()).limit(1)
    ).scalar_one_or_none() if quote else None

    change = None
    change_pct = None
    if quote and prev_quote and prev_quote.close and prev_quote.close != 0:
        change = round(quote.close - prev_quote.close, 2)
        change_pct = round(change / prev_quote.close * 100, 2)

    # Latest metrics
    metric = db.execute(
        select(CalculatedMetric).where(CalculatedMetric.code == code)
        .order_by(CalculatedMetric.date.desc()).limit(1)
    ).scalar_one_or_none()

    # Latest financial
    fin = db.execute(
        select(FinancialStatement).where(FinancialStatement.code == code)
        .order_by(FinancialStatement.disclosed_date.desc()).limit(1)
    ).scalar_one_or_none()

    # 52-week high/low
    from datetime import timedelta
    one_year_ago = date.today() - timedelta(days=365)
    high_52w = db.execute(
        select(func.max(DailyQuote.high)).where(
            DailyQuote.code == code, DailyQuote.date >= one_year_ago
        )
    ).scalar()
    low_52w = db.execute(
        select(func.min(DailyQuote.low)).where(
            DailyQuote.code == code, DailyQuote.date >= one_year_ago,
            DailyQuote.low > 0,
        )
    ).scalar()

    return {
        "code": stock.code,
        "name": stock.name,
        "market_segment": stock.market_segment,
        "sector_17": stock.sector_17,
        "sector_33": stock.sector_33,
        "quote": {
            "date": quote.date.isoformat() if quote else None,
            "open": quote.open if quote else None,
            "high": quote.high if quote else None,
            "low": quote.low if quote else None,
            "close": quote.close if quote else None,
            "volume": quote.volume if quote else None,
            "change": change,
            "change_pct": change_pct,
        },
        "metrics": {
            "per": metric.per if metric else None,
            "pbr": metric.pbr if metric else None,
            "roe": metric.roe if metric else None,
            "dividend_yield": metric.dividend_yield if metric else None,
            "market_cap": metric.market_cap if metric else None,
            "turnover_days_20": metric.turnover_days if metric else None,
            "avg_volume_20d": metric.avg_volume_20d if metric else None,
            "avg_volume_60d": metric.avg_volume_60d if metric else None,
            "volatility_20d": metric.volatility_20d if metric else None,
            "operating_margin": metric.operating_margin if metric else None,
            "ytd_return": metric.ytd_return if metric else None,
        },
        "financial": {
            "equity_ratio": fin.equity_ratio if fin else None,
            "shares_outstanding": fin.shares_outstanding if fin else None,
            "fiscal_year": fin.fiscal_year if fin else None,
            "disclosed_date": fin.disclosed_date.isoformat() if fin and fin.disclosed_date else None,
            "net_sales": fin.net_sales if fin else None,
            "operating_profit": fin.operating_profit if fin else None,
            "net_income": fin.net_income if fin else None,
            "eps": fin.eps if fin else None,
            "bps": fin.bps if fin else None,
            "dividend_forecast": fin.dividend_forecast if fin else None,
        },
        "high_52w": high_52w,
        "low_52w": low_52w,
    }


@router.get("/{code}/quotes")
def get_quotes(
    code: str,
    db: Session = Depends(get_db),
    from_date: str | None = Query(None, alias="from"),
    to_date: str | None = Query(None, alias="to"),
):
    """Get price history for a stock."""
    query = select(DailyQuote).where(DailyQuote.code == code)

    if from_date:
        query = query.where(DailyQuote.date >= date.fromisoformat(from_date))
    if to_date:
        query = query.where(DailyQuote.date <= date.fromisoformat(to_date))

    query = query.order_by(DailyQuote.date.asc())
    rows = db.execute(query).scalars().all()

    return [
        {
            "date": r.date.isoformat(),
            "open": r.open,
            "high": r.high,
            "low": r.low,
            "close": r.close,
            "volume": r.volume,
            "turnover_value": r.turnover_value,
        }
        for r in rows
    ]


@router.get("/{code}/financials")
def get_financials(code: str, db: Session = Depends(get_db)):
    """Get financial statement history."""
    rows = db.execute(
        select(FinancialStatement).where(FinancialStatement.code == code)
        .order_by(FinancialStatement.fiscal_year.desc(), FinancialStatement.type_of_document.desc())
    ).scalars().all()

    return [
        {
            "id": r.id,
            "fiscal_year": r.fiscal_year,
            "type_of_document": r.type_of_document,
            "disclosed_date": r.disclosed_date.isoformat() if r.disclosed_date else None,
            "net_sales": r.net_sales,
            "operating_profit": r.operating_profit,
            "ordinary_profit": r.ordinary_profit,
            "net_income": r.net_income,
            "eps": r.eps,
            "bps": r.bps,
            "total_assets": r.total_assets,
            "equity": r.equity,
            "equity_ratio": r.equity_ratio,
            "shares_outstanding": r.shares_outstanding,
            "dividend_forecast": r.dividend_forecast,
            "forecast_net_sales": r.forecast_net_sales,
            "forecast_operating_profit": r.forecast_operating_profit,
            "forecast_net_income": r.forecast_net_income,
            "forecast_eps": r.forecast_eps,
            "forecast_dividend": r.forecast_dividend,
        }
        for r in rows
    ]


@router.get("/{code}/metrics")
def get_metrics(code: str, db: Session = Depends(get_db)):
    """Get calculated metrics history."""
    rows = db.execute(
        select(CalculatedMetric).where(CalculatedMetric.code == code)
        .order_by(CalculatedMetric.date.desc())
    ).scalars().all()

    return [
        {
            "date": r.date.isoformat(),
            "per": r.per,
            "pbr": r.pbr,
            "roe": r.roe,
            "dividend_yield": r.dividend_yield,
            "market_cap": r.market_cap,
            "turnover_days": r.turnover_days,
            "avg_volume_20d": r.avg_volume_20d,
            "avg_volume_60d": r.avg_volume_60d,
            "volatility_20d": r.volatility_20d,
        }
        for r in rows
    ]


@router.get("/{code}/technicals")
def get_technicals(
    code: str,
    db: Session = Depends(get_db),
    from_date: str | None = Query(None, alias="from"),
    to_date: str | None = Query(None, alias="to"),
    indicators: str = "sma,ema,rsi,macd,bollinger,ichimoku",
):
    """Get technical indicators for a stock."""
    to_d = date.fromisoformat(to_date) if to_date else date.today()
    from_d = date.fromisoformat(from_date) if from_date else date(to_d.year - 1, to_d.month, to_d.day)

    ind_list = [i.strip() for i in indicators.split(",") if i.strip()]
    return calculate_technicals(db, code, from_d, to_d, ind_list)


@router.get("/{code}/impact")
def get_impact(
    code: str,
    db: Session = Depends(get_db),
    quantity: int = Query(100000),
    days: int = Query(1),
    participation_rate: float = Query(0.1),
    vol_period: int = Query(20),
):
    """Run impact analysis simulation."""
    stock = db.get(Stock, code)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    result = calculate_impact(
        db, code, quantity, days, participation_rate, vol_period
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    result["name"] = stock.name
    return result

"""Screening engine — builds SQL queries from filter conditions."""

import logging
from datetime import date

from sqlalchemy import select, and_, or_, func, case
from sqlalchemy.orm import Session

from backend.models import Stock, DailyQuote, CalculatedMetric, FinancialStatement

logger = logging.getLogger(__name__)

# Map of field names to (table, column) pairs
FIELD_MAP = {
    # Price
    "close": (DailyQuote, "close"),
    # Valuation
    "per": (CalculatedMetric, "per"),
    "pbr": (CalculatedMetric, "pbr"),
    "dividend_yield": (CalculatedMetric, "dividend_yield"),
    # Profitability
    "roe": (CalculatedMetric, "roe"),
    "operating_margin": (CalculatedMetric, "operating_margin"),
    "ordinary_margin": (CalculatedMetric, "ordinary_margin"),
    # Financial health
    "equity_ratio": (FinancialStatement, "equity_ratio"),
    # Scale
    "market_cap": (CalculatedMetric, "market_cap"),
    "net_sales": (FinancialStatement, "net_sales"),
    # Liquidity
    "turnover_days": (CalculatedMetric, "turnover_days"),
    "avg_volume_20d": (CalculatedMetric, "avg_volume_20d"),
    # Technical (pre-calculated)
    "ytd_return": (CalculatedMetric, "ytd_return"),
    "volatility_20d": (CalculatedMetric, "volatility_20d"),
    # Attributes
    "market_segment": (Stock, "market_segment"),
    "sector_17": (Stock, "sector_17"),
    "sector_33": (Stock, "sector_33"),
    "name": (Stock, "name"),
}

OPERATORS = {
    "gt": lambda col, val: col > val,
    "lt": lambda col, val: col < val,
    "gte": lambda col, val: col >= val,
    "lte": lambda col, val: col <= val,
    "eq": lambda col, val: col == val,
    "between": lambda col, val: and_(col >= val[0], col <= val[1]),
    "contains": lambda col, val: col.contains(val),
    "in": lambda col, val: col.in_(val),
}


def execute_screening(db: Session, request: dict) -> dict:
    """Execute a screening search and return paginated results."""
    conditions = request.get("conditions", [])
    group_logic = request.get("group_logic", "and")
    sort_by = request.get("sort_by", "code")
    sort_order = request.get("sort_order", "asc")
    page = request.get("page", 1)
    per_page = request.get("per_page", 50)
    market_segments = request.get("market_segments", [])
    sectors_33 = request.get("sectors_33", [])

    # Get latest metrics date
    latest_date = db.execute(select(func.max(CalculatedMetric.date))).scalar()
    latest_quote_date = db.execute(select(func.max(DailyQuote.date))).scalar()

    # Base query: join stocks, latest quotes, latest metrics, latest financials
    # Using subqueries for latest records
    latest_quote_sub = (
        select(
            DailyQuote.code,
            DailyQuote.close,
            DailyQuote.volume,
            DailyQuote.turnover_value,
            DailyQuote.date.label("quote_date"),
        ).where(
            DailyQuote.date == latest_quote_date
        ).subquery("lq")
    )

    latest_metric_sub = (
        select(CalculatedMetric).where(
            CalculatedMetric.date == latest_date
        ).subquery("lm")
    )

    # Build the base query
    query = (
        select(
            Stock.code,
            Stock.name,
            Stock.market_segment,
            Stock.sector_33,
            latest_quote_sub.c.close,
            latest_metric_sub.c.per,
            latest_metric_sub.c.pbr,
            latest_metric_sub.c.roe,
            latest_metric_sub.c.dividend_yield,
            latest_metric_sub.c.turnover_days,
            latest_metric_sub.c.market_cap,
            latest_metric_sub.c.operating_margin,
            latest_metric_sub.c.ordinary_margin,
            latest_metric_sub.c.ytd_return,
            latest_metric_sub.c.avg_volume_20d,
            latest_metric_sub.c.volatility_20d,
        )
        .outerjoin(latest_quote_sub, Stock.code == latest_quote_sub.c.code)
        .outerjoin(latest_metric_sub, Stock.code == latest_metric_sub.c.code)
        .where(Stock.is_active == True)
    )

    # Market/sector filters
    if market_segments:
        query = query.where(Stock.market_segment.in_(market_segments))
    if sectors_33:
        query = query.where(Stock.sector_33.in_(sectors_33))

    # Build condition filters
    if conditions:
        groups: dict[int, list] = {}
        for cond in conditions:
            grp = cond.get("group", 1)
            groups.setdefault(grp, []).append(cond)

        group_filters = []
        for grp_num, grp_conds in groups.items():
            filters = []
            for cond in grp_conds:
                field = cond.get("field")
                operator = cond.get("operator")
                value = cond.get("value")

                col = _resolve_column(field, latest_quote_sub, latest_metric_sub)
                if col is None:
                    continue

                op_func = OPERATORS.get(operator)
                if op_func:
                    filters.append(op_func(col, value))

            if filters:
                group_filters.append(and_(*filters))

        if group_filters:
            if group_logic == "or":
                query = query.where(or_(*group_filters))
            else:
                query = query.where(and_(*group_filters))

    # Count total
    from sqlalchemy import text
    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar() or 0

    # Sort
    sort_col = _resolve_column(sort_by, latest_quote_sub, latest_metric_sub)
    if sort_col is not None:
        query = query.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())
    else:
        query = query.order_by(Stock.code.asc())

    # Paginate
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    rows = db.execute(query).all()

    # Compute change_pct for each result
    results = []
    for row in rows:
        change_pct = _calc_change_pct(db, row.code, latest_quote_date)
        results.append({
            "code": row.code,
            "name": row.name,
            "market_segment": row.market_segment,
            "sector_33": row.sector_33,
            "close": row.close,
            "change_pct": change_pct,
            "per": row.per,
            "pbr": row.pbr,
            "roe": row.roe,
            "dividend_yield": row.dividend_yield,
            "turnover_days_20": row.turnover_days,
            "market_cap": row.market_cap,
            "date": latest_quote_date.isoformat() if latest_quote_date else None,
        })

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "results": results,
    }


def _resolve_column(field, quote_sub, metric_sub):
    """Resolve a field name to a column reference."""
    mapping = {
        "close": quote_sub.c.close,
        "per": metric_sub.c.per,
        "pbr": metric_sub.c.pbr,
        "roe": metric_sub.c.roe,
        "dividend_yield": metric_sub.c.dividend_yield,
        "turnover_days": metric_sub.c.turnover_days,
        "market_cap": metric_sub.c.market_cap,
        "operating_margin": metric_sub.c.operating_margin,
        "ordinary_margin": metric_sub.c.ordinary_margin,
        "ytd_return": metric_sub.c.ytd_return,
        "avg_volume_20d": metric_sub.c.avg_volume_20d,
        "volatility_20d": metric_sub.c.volatility_20d,
        "code": Stock.code,
        "name": Stock.name,
        "market_segment": Stock.market_segment,
        "sector_33": Stock.sector_33,
    }
    return mapping.get(field)


def _calc_change_pct(db: Session, code: str, ref_date) -> float | None:
    """Calculate day-over-day change percentage."""
    if not ref_date:
        return None
    recent = db.execute(
        select(DailyQuote.close).where(
            DailyQuote.code == code,
            DailyQuote.date <= ref_date,
            DailyQuote.close.isnot(None),
        ).order_by(DailyQuote.date.desc()).limit(2)
    ).scalars().all()

    if len(recent) < 2 or not recent[0] or not recent[1] or recent[1] == 0:
        return None

    return round((recent[0] - recent[1]) / recent[1] * 100, 2)

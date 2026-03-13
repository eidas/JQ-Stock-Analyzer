"""Portfolio management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Portfolio, PortfolioItem, Stock, DailyQuote, FinancialStatement

router = APIRouter()


class PortfolioCreate(BaseModel):
    name: str
    description: str | None = None


class PortfolioItemCreate(BaseModel):
    code: str
    shares: int
    avg_cost: float
    acquired_date: str | None = None
    memo: str | None = None


class PortfolioItemUpdate(BaseModel):
    shares: int | None = None
    avg_cost: float | None = None
    memo: str | None = None


@router.get("")
def list_portfolios(db: Session = Depends(get_db)):
    """List all portfolios with summary."""
    portfolios = db.query(Portfolio).order_by(Portfolio.created_at.desc()).all()
    results = []
    for p in portfolios:
        total_value, total_cost = _calc_portfolio_totals(db, p.id)
        pnl = total_value - total_cost if total_value and total_cost else None
        pnl_pct = (pnl / total_cost * 100) if pnl is not None and total_cost and total_cost > 0 else None
        results.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "total_value": total_value,
            "total_cost": total_cost,
            "pnl": round(pnl, 2) if pnl is not None else None,
            "pnl_pct": round(pnl_pct, 2) if pnl_pct is not None else None,
            "item_count": len(p.items),
        })
    return results


@router.post("")
def create_portfolio(data: PortfolioCreate, db: Session = Depends(get_db)):
    """Create a new portfolio."""
    p = Portfolio(name=data.name, description=data.description)
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"id": p.id, "name": p.name}


@router.get("/{portfolio_id}")
def get_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    """Get portfolio detail with holdings."""
    p = db.get(Portfolio, portfolio_id)
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    items = []
    total_value = 0
    for item in p.items:
        stock = db.get(Stock, item.code)
        latest_quote = db.execute(
            select(DailyQuote).where(DailyQuote.code == item.code)
            .order_by(DailyQuote.date.desc()).limit(1)
        ).scalar_one_or_none()

        current_price = latest_quote.close if latest_quote and latest_quote.close else None
        eval_amount = current_price * item.shares if current_price and item.shares else None
        cost_amount = item.avg_cost * item.shares if item.avg_cost and item.shares else None
        pnl = eval_amount - cost_amount if eval_amount and cost_amount else None
        pnl_pct = (pnl / cost_amount * 100) if pnl is not None and cost_amount and cost_amount > 0 else None

        # Dividend yield on cost
        fin = db.execute(
            select(FinancialStatement).where(FinancialStatement.code == item.code)
            .order_by(FinancialStatement.disclosed_date.desc()).limit(1)
        ).scalar_one_or_none()
        div_yield_cost = (fin.dividend_forecast / item.avg_cost * 100) if fin and fin.dividend_forecast and item.avg_cost and item.avg_cost > 0 else None

        if eval_amount:
            total_value += eval_amount

        items.append({
            "id": item.id,
            "code": item.code,
            "name": stock.name if stock else None,
            "sector_33": stock.sector_33 if stock else None,
            "shares": item.shares,
            "avg_cost": item.avg_cost,
            "current_price": current_price,
            "eval_amount": round(eval_amount, 2) if eval_amount else None,
            "pnl": round(pnl, 2) if pnl is not None else None,
            "pnl_pct": round(pnl_pct, 2) if pnl_pct is not None else None,
            "dividend_yield_cost": round(div_yield_cost, 2) if div_yield_cost else None,
            "acquired_date": item.acquired_date.isoformat() if item.acquired_date else None,
            "memo": item.memo,
        })

    # Calculate allocation ratios
    for item in items:
        if item["eval_amount"] and total_value > 0:
            item["allocation_pct"] = round(item["eval_amount"] / total_value * 100, 2)
        else:
            item["allocation_pct"] = None

    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "total_value": round(total_value, 2),
        "items": items,
    }


@router.put("/{portfolio_id}")
def update_portfolio(portfolio_id: int, data: PortfolioCreate, db: Session = Depends(get_db)):
    """Update portfolio name/description."""
    p = db.get(Portfolio, portfolio_id)
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    p.name = data.name
    if data.description is not None:
        p.description = data.description
    db.commit()
    return {"id": p.id, "name": p.name}


@router.delete("/{portfolio_id}")
def delete_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    """Delete a portfolio and all its items."""
    p = db.get(Portfolio, portfolio_id)
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    db.delete(p)
    db.commit()
    return {"status": "deleted"}


@router.post("/{portfolio_id}/items")
def add_item(portfolio_id: int, data: PortfolioItemCreate, db: Session = Depends(get_db)):
    """Add a stock to a portfolio."""
    p = db.get(Portfolio, portfolio_id)
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    from datetime import date as date_type
    acquired = date_type.fromisoformat(data.acquired_date) if data.acquired_date else None

    item = PortfolioItem(
        portfolio_id=portfolio_id,
        code=data.code,
        shares=data.shares,
        avg_cost=data.avg_cost,
        acquired_date=acquired,
        memo=data.memo,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "code": item.code}


@router.put("/{portfolio_id}/items/{item_id}")
def update_item(portfolio_id: int, item_id: int, data: PortfolioItemUpdate, db: Session = Depends(get_db)):
    """Update a portfolio item."""
    item = db.get(PortfolioItem, item_id)
    if not item or item.portfolio_id != portfolio_id:
        raise HTTPException(status_code=404, detail="Item not found")
    if data.shares is not None:
        item.shares = data.shares
    if data.avg_cost is not None:
        item.avg_cost = data.avg_cost
    if data.memo is not None:
        item.memo = data.memo
    db.commit()
    return {"id": item.id}


@router.delete("/{portfolio_id}/items/{item_id}")
def delete_item(portfolio_id: int, item_id: int, db: Session = Depends(get_db)):
    """Remove a stock from a portfolio."""
    item = db.get(PortfolioItem, item_id)
    if not item or item.portfolio_id != portfolio_id:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"status": "deleted"}


@router.get("/{portfolio_id}/performance")
def get_performance(portfolio_id: int, db: Session = Depends(get_db)):
    """Calculate portfolio performance over time."""
    p = db.get(Portfolio, portfolio_id)
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # Simple: return daily total values
    from datetime import timedelta
    from sqlalchemy import func

    codes = [item.code for item in p.items]
    if not codes:
        return {"dates": [], "values": []}

    shares_map = {item.code: item.shares or 0 for item in p.items}

    # Get date range
    min_date = db.execute(
        select(func.min(DailyQuote.date)).where(DailyQuote.code.in_(codes))
    ).scalar()
    max_date = db.execute(
        select(func.max(DailyQuote.date)).where(DailyQuote.code.in_(codes))
    ).scalar()

    if not min_date or not max_date:
        return {"dates": [], "values": []}

    # Get all quotes for portfolio stocks
    all_quotes = db.execute(
        select(DailyQuote.code, DailyQuote.date, DailyQuote.close)
        .where(DailyQuote.code.in_(codes))
        .order_by(DailyQuote.date.asc())
    ).all()

    # Build date→value map
    from collections import defaultdict
    date_values = defaultdict(float)
    for q in all_quotes:
        if q.close and q.code in shares_map:
            date_values[q.date] += q.close * shares_map[q.code]

    sorted_dates = sorted(date_values.keys())
    return {
        "dates": [d.isoformat() for d in sorted_dates],
        "values": [round(date_values[d], 2) for d in sorted_dates],
    }


def _calc_portfolio_totals(db: Session, portfolio_id: int):
    """Calculate total market value and total cost for a portfolio."""
    items = db.query(PortfolioItem).filter(PortfolioItem.portfolio_id == portfolio_id).all()
    total_value = 0
    total_cost = 0
    for item in items:
        latest = db.execute(
            select(DailyQuote.close).where(DailyQuote.code == item.code)
            .order_by(DailyQuote.date.desc()).limit(1)
        ).scalar()
        if latest and item.shares:
            total_value += latest * item.shares
        if item.avg_cost and item.shares:
            total_cost += item.avg_cost * item.shares
    return total_value, total_cost

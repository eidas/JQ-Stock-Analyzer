"""Export API endpoints — CSV download for screening results and portfolios."""

import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.screening_service import execute_screening
from backend.routers.portfolios import _calc_portfolio_totals
from backend.models import Portfolio, PortfolioItem, Stock, DailyQuote

router = APIRouter()


class ExportScreeningRequest(BaseModel):
    conditions: list = []
    group_logic: str = "and"
    sort_by: str = "code"
    sort_order: str = "asc"
    market_segments: list[str] = []
    sectors_33: list[str] = []


@router.post("/screening")
def export_screening(request: ExportScreeningRequest, db: Session = Depends(get_db)):
    """Export screening results as CSV (all results, no pagination)."""
    req_dict = request.model_dump()
    req_dict["page"] = 1
    req_dict["per_page"] = 100000  # Get all results
    result = execute_screening(db, req_dict)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "銘柄コード", "銘柄名", "市場区分", "業種", "終値",
        "前日比(%)", "PER", "PBR", "ROE", "配当利回り",
        "回転日数(20日)", "時価総額", "日付"
    ])
    for r in result.get("results", []):
        writer.writerow([
            r.get("code"), r.get("name"), r.get("market_segment"),
            r.get("sector_33"), r.get("close"), r.get("change_pct"),
            r.get("per"), r.get("pbr"), r.get("roe"),
            r.get("dividend_yield"), r.get("turnover_days_20"),
            r.get("market_cap"), r.get("date"),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=screening_results.csv"},
    )


@router.get("/portfolio/{portfolio_id}")
def export_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    """Export portfolio holdings as CSV."""
    from sqlalchemy import select

    portfolio = db.get(Portfolio, portfolio_id)
    if not portfolio:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Portfolio not found")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "銘柄コード", "銘柄名", "保有株数", "平均取得単価",
        "現在値", "評価額", "損益額", "損益率(%)", "取得日", "メモ"
    ])

    for item in portfolio.items:
        stock = db.get(Stock, item.code)
        latest = db.execute(
            select(DailyQuote.close).where(DailyQuote.code == item.code)
            .order_by(DailyQuote.date.desc()).limit(1)
        ).scalar()

        current = latest or 0
        eval_amt = current * item.shares if item.shares else 0
        cost_amt = (item.avg_cost or 0) * (item.shares or 0)
        pnl = eval_amt - cost_amt
        pnl_pct = (pnl / cost_amt * 100) if cost_amt > 0 else 0

        writer.writerow([
            item.code,
            stock.name if stock else "",
            item.shares,
            item.avg_cost,
            current,
            round(eval_amt, 2),
            round(pnl, 2),
            round(pnl_pct, 2),
            item.acquired_date.isoformat() if item.acquired_date else "",
            item.memo or "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=portfolio_{portfolio_id}.csv"},
    )

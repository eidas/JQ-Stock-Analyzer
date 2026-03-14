"""Master data API endpoints — sectors, markets, stock search."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, distinct, func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Stock

router = APIRouter()


@router.get("/sectors")
def list_sectors(db: Session = Depends(get_db)):
    """Get distinct sector lists."""
    sectors_17 = db.execute(
        select(distinct(Stock.sector_17)).where(Stock.sector_17.isnot(None)).order_by(Stock.sector_17)
    ).scalars().all()
    sectors_33 = db.execute(
        select(distinct(Stock.sector_33)).where(Stock.sector_33.isnot(None)).order_by(Stock.sector_33)
    ).scalars().all()
    return {"sector_17": sectors_17, "sector_33": sectors_33}


@router.get("/markets")
def list_markets(db: Session = Depends(get_db)):
    """Get distinct market segments."""
    markets = db.execute(
        select(distinct(Stock.market_segment)).where(Stock.market_segment.isnot(None)).order_by(Stock.market_segment)
    ).scalars().all()
    return {"markets": markets}


@router.get("/stocks/search")
def search_stocks(
    q: str = Query("", min_length=0),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
):
    """Incremental stock search by code or name."""
    if not q:
        return []

    results = db.execute(
        select(Stock.code, Stock.name, Stock.market_segment, Stock.sector_33)
        .where(
            Stock.is_active == True,
            (Stock.code.contains(q) | Stock.name.contains(q)),
        )
        .order_by(Stock.code.asc())
        .limit(limit)
    ).all()

    return [
        {
            "code": r.code,
            "name": r.name,
            "market_segment": r.market_segment,
            "sector_33": r.sector_33,
        }
        for r in results
    ]

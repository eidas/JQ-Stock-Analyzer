"""Data synchronization service — fetches data from J-Quants API and stores it in the DB."""

import asyncio
import logging
from datetime import date, datetime, timedelta

import pandas as pd
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models import Stock, DailyQuote, FinancialStatement, DataSyncLog
from backend.services.jquants_client import JQuantsClient

logger = logging.getLogger(__name__)

# Lock flag to prevent concurrent sync operations
_sync_lock = asyncio.Lock()
_current_sync_id: int | None = None


def _business_days(start: date, end: date) -> list[date]:
    """Generate list of weekday dates between start and end (inclusive)."""
    days = []
    current = start
    while current <= end:
        if current.weekday() < 5:  # Mon-Fri
            days.append(current)
        current += timedelta(days=1)
    return days


def _get_last_sync_date(db: Session, sync_type: str) -> date | None:
    """Get the most recent successfully synced date for a given type."""
    result = db.execute(
        select(func.max(DataSyncLog.target_date)).where(
            DataSyncLog.sync_type == sync_type,
            DataSyncLog.status == "success",
        )
    ).scalar()
    return result


def sync_listings(db: Session, client: JQuantsClient, sync_log_id: int | None = None) -> int:
    """Sync stock master data (銘柄マスタ)."""
    logger.info("Starting listings sync")
    df = client.get_listed_stocks()
    if df is None or df.empty:
        return 0

    count = 0
    col_map = {
        "Code": "code",
        "CompanyName": "name",
        "Sector17CodeName": "sector_17",
        "Sector33CodeName": "sector_33",
        "MarketCodeName": "market_segment",
    }

    for _, row in df.iterrows():
        code = str(row.get("Code", ""))[:4]
        if not code or len(code) < 4:
            continue
        existing = db.get(Stock, code)
        if existing:
            existing.name = row.get("CompanyName", existing.name)
            existing.sector_17 = row.get("Sector17CodeName", existing.sector_17)
            existing.sector_33 = row.get("Sector33CodeName", existing.sector_33)
            existing.market_segment = row.get("MarketCodeName", existing.market_segment)
            existing.is_active = True
            existing.updated_at = datetime.utcnow()
        else:
            db.add(Stock(
                code=code,
                name=row.get("CompanyName", ""),
                sector_17=row.get("Sector17CodeName"),
                sector_33=row.get("Sector33CodeName"),
                market_segment=row.get("MarketCodeName"),
                is_active=True,
            ))
        count += 1

    db.commit()
    logger.info("Listings sync completed: %d records", count)
    return count


def sync_quotes(
    db: Session,
    client: JQuantsClient,
    from_date: date | None = None,
    to_date: date | None = None,
    sync_log_id: int | None = None,
) -> int:
    """Sync daily quotes from J-Quants API."""
    if to_date is None:
        to_date = date.today()
    if from_date is None:
        last = _get_last_sync_date(db, "quotes")
        from_date = (last + timedelta(days=1)) if last else (to_date - timedelta(days=365 * 5))

    days = _business_days(from_date, to_date)
    total_days = len(days)
    if total_days == 0:
        return 0

    logger.info("Syncing quotes: %s to %s (%d days)", from_date, to_date, total_days)
    total_records = 0

    for i, day in enumerate(days):
        try:
            df = client.get_daily_quotes(day.isoformat())
            if df is None or df.empty:
                continue

            records = 0
            for _, row in df.iterrows():
                code = str(row.get("Code", ""))[:4]
                if not code or len(code) < 4:
                    continue
                trade_date = pd.to_datetime(row.get("Date", day)).date() if "Date" in row.index else day

                existing = db.execute(
                    select(DailyQuote).where(
                        DailyQuote.code == code,
                        DailyQuote.date == trade_date,
                    )
                ).scalar_one_or_none()

                if existing:
                    continue

                db.add(DailyQuote(
                    code=code,
                    date=trade_date,
                    open=_safe_float(row.get("AdjustmentOpen")),
                    high=_safe_float(row.get("AdjustmentHigh")),
                    low=_safe_float(row.get("AdjustmentLow")),
                    close=_safe_float(row.get("AdjustmentClose")),
                    volume=_safe_int(row.get("AdjustmentVolume")),
                    turnover_value=_safe_float(row.get("TurnoverValue")),
                    adjustment_factor=_safe_float(row.get("AdjustmentFactor")),
                ))
                records += 1

            db.commit()
            total_records += records

            # Update progress
            if sync_log_id:
                pct = ((i + 1) / total_days) * 100
                _update_sync_progress(db, sync_log_id, pct, f"株価取得中 {i + 1}/{total_days}日")

        except Exception as e:
            logger.error("Error syncing quotes for %s: %s", day, e)
            db.rollback()

    return total_records


def sync_statements(
    db: Session,
    client: JQuantsClient,
    from_date: date | None = None,
    to_date: date | None = None,
    sync_log_id: int | None = None,
) -> int:
    """Sync financial statements."""
    if to_date is None:
        to_date = date.today()
    if from_date is None:
        last = _get_last_sync_date(db, "statements")
        from_date = (last + timedelta(days=1)) if last else (to_date - timedelta(days=365 * 5))

    days = _business_days(from_date, to_date)
    total_days = len(days)
    if total_days == 0:
        return 0

    logger.info("Syncing statements: %s to %s (%d days)", from_date, to_date, total_days)
    total_records = 0

    for i, day in enumerate(days):
        try:
            df = client.get_financial_statements(day.isoformat())
            if df is None or df.empty:
                continue

            code_col = "LocalCode" if "LocalCode" in df.columns else "Code"
            records = 0
            for _, row in df.iterrows():
                code = str(row.get(code_col, ""))[:4]
                if not code or len(code) < 4:
                    continue

                fiscal_year = row.get("CurrentFiscalYearEndDate", "")
                if fiscal_year and len(str(fiscal_year)) >= 7:
                    fiscal_year = str(fiscal_year)[:7]  # YYYY-MM
                type_of_doc = row.get("TypeOfDocument", "")

                existing = db.execute(
                    select(FinancialStatement).where(
                        FinancialStatement.code == code,
                        FinancialStatement.fiscal_year == fiscal_year,
                        FinancialStatement.type_of_document == type_of_doc,
                    )
                ).scalar_one_or_none()

                if existing:
                    # UPSERT: update existing record
                    _update_financial(existing, row)
                else:
                    db.add(_create_financial(code, fiscal_year, type_of_doc, row, day))
                records += 1

            db.commit()
            total_records += records

            if sync_log_id:
                pct = ((i + 1) / total_days) * 100
                _update_sync_progress(db, sync_log_id, pct, f"財務データ取得中 {i + 1}/{total_days}日")

        except Exception as e:
            logger.error("Error syncing statements for %s: %s", day, e)
            db.rollback()

    return total_records


async def sync_all_async(api_key: str | None = None):
    """Run full sync (listings → quotes → statements → metrics) in background."""
    global _current_sync_id

    if _sync_lock.locked():
        logger.warning("Sync already in progress")
        return

    async with _sync_lock:
        db = SessionLocal()
        try:
            log = DataSyncLog(
                sync_type="all",
                status="running",
                progress_pct=0.0,
                current_step="同期開始",
                started_at=datetime.utcnow(),
            )
            db.add(log)
            db.commit()
            db.refresh(log)
            _current_sync_id = log.id

            client = JQuantsClient(api_key)

            # Step 1: Listings
            _update_sync_progress(db, log.id, 5, "銘柄マスタ取得中...")
            await asyncio.to_thread(sync_listings, db, client, log.id)

            # Step 2: Quotes
            _update_sync_progress(db, log.id, 10, "株価データ取得中...")
            count_q = await asyncio.to_thread(sync_quotes, db, client, None, None, log.id)

            # Step 3: Statements
            _update_sync_progress(db, log.id, 70, "財務データ取得中...")
            count_s = await asyncio.to_thread(sync_statements, db, client, None, None, log.id)

            # Step 4: Metrics recalculation
            _update_sync_progress(db, log.id, 90, "指標再計算中...")
            from backend.services.metrics_service import batch_calculate
            await asyncio.to_thread(batch_calculate, db)

            # Done
            log.status = "success"
            log.progress_pct = 100.0
            log.current_step = "完了"
            log.records_count = count_q + count_s
            log.completed_at = datetime.utcnow()
            db.commit()

        except Exception as e:
            logger.error("Sync failed: %s", e)
            if _current_sync_id:
                log_entry = db.get(DataSyncLog, _current_sync_id)
                if log_entry:
                    log_entry.status = "error"
                    log_entry.error_message = str(e)
                    log_entry.completed_at = datetime.utcnow()
                    db.commit()
        finally:
            _current_sync_id = None
            db.close()


def get_sync_status(db: Session) -> dict:
    """Get the current sync status."""
    # Get most recent sync log
    log = db.execute(
        select(DataSyncLog).order_by(DataSyncLog.id.desc()).limit(1)
    ).scalar_one_or_none()

    if not log:
        return {"status": "idle", "progress_pct": 0, "current_step": "未同期"}

    return {
        "id": log.id,
        "sync_type": log.sync_type,
        "status": log.status,
        "progress_pct": log.progress_pct or 0,
        "current_step": log.current_step or "",
        "records_count": log.records_count,
        "error_message": log.error_message,
        "started_at": log.started_at.isoformat() if log.started_at else None,
        "completed_at": log.completed_at.isoformat() if log.completed_at else None,
    }


def _update_sync_progress(db: Session, log_id: int, pct: float, step: str):
    log = db.get(DataSyncLog, log_id)
    if log:
        log.progress_pct = pct
        log.current_step = step
        db.commit()


def _safe_float(val) -> float | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _safe_int(val) -> int | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def _update_financial(existing: FinancialStatement, row: pd.Series):
    existing.net_sales = _safe_float(row.get("NetSales"))
    existing.operating_profit = _safe_float(row.get("OperatingProfit"))
    existing.ordinary_profit = _safe_float(row.get("OrdinaryProfit"))
    existing.net_income = _safe_float(row.get("Profit"))
    existing.eps = _safe_float(row.get("EarningsPerShare"))
    existing.bps = _safe_float(row.get("BookValuePerShare"))
    existing.total_assets = _safe_float(row.get("TotalAssets"))
    existing.equity = _safe_float(row.get("Equity"))
    existing.equity_ratio = _safe_float(row.get("EquityToAssetRatio"))
    existing.shares_outstanding = _safe_int(row.get("NumberOfIssuedAndOutstandingSharesAtTheEndOfFiscalYearIncludingTreasuryStock"))
    existing.dividend_forecast = _safe_float(row.get("DividendPerShareAnnual"))
    existing.forecast_net_sales = _safe_float(row.get("ForecastNetSales"))
    existing.forecast_operating_profit = _safe_float(row.get("ForecastOperatingProfit"))
    existing.forecast_ordinary_profit = _safe_float(row.get("ForecastOrdinaryProfit"))
    existing.forecast_net_income = _safe_float(row.get("ForecastProfit"))
    existing.forecast_eps = _safe_float(row.get("ForecastEarningsPerShare"))
    existing.forecast_dividend = _safe_float(row.get("ForecastDividendPerShareAnnual"))


def _create_financial(
    code: str, fiscal_year: str, type_of_doc: str, row: pd.Series, day: date
) -> FinancialStatement:
    disclosed = row.get("DisclosedDate")
    if disclosed:
        try:
            disclosed = pd.to_datetime(disclosed).date()
        except Exception:
            disclosed = day
    else:
        disclosed = day

    return FinancialStatement(
        code=code,
        disclosed_date=disclosed,
        fiscal_year=fiscal_year,
        type_of_document=type_of_doc,
        net_sales=_safe_float(row.get("NetSales")),
        operating_profit=_safe_float(row.get("OperatingProfit")),
        ordinary_profit=_safe_float(row.get("OrdinaryProfit")),
        net_income=_safe_float(row.get("Profit")),
        eps=_safe_float(row.get("EarningsPerShare")),
        bps=_safe_float(row.get("BookValuePerShare")),
        total_assets=_safe_float(row.get("TotalAssets")),
        equity=_safe_float(row.get("Equity")),
        equity_ratio=_safe_float(row.get("EquityToAssetRatio")),
        shares_outstanding=_safe_int(row.get("NumberOfIssuedAndOutstandingSharesAtTheEndOfFiscalYearIncludingTreasuryStock")),
        dividend_forecast=_safe_float(row.get("DividendPerShareAnnual")),
        forecast_net_sales=_safe_float(row.get("ForecastNetSales")),
        forecast_operating_profit=_safe_float(row.get("ForecastOperatingProfit")),
        forecast_ordinary_profit=_safe_float(row.get("ForecastOrdinaryProfit")),
        forecast_net_income=_safe_float(row.get("ForecastProfit")),
        forecast_eps=_safe_float(row.get("ForecastEarningsPerShare")),
        forecast_dividend=_safe_float(row.get("ForecastDividendPerShareAnnual")),
    )

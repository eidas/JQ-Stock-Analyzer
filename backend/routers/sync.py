"""Data sync API endpoints."""

import asyncio

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.sync_service import sync_all_async, get_sync_status

router = APIRouter()


@router.post("/quotes")
async def trigger_quotes_sync():
    """Trigger daily quotes sync (202 Accepted)."""
    asyncio.create_task(sync_all_async())
    return {"status": "accepted", "message": "Quotes sync started"}


@router.post("/statements")
async def trigger_statements_sync():
    """Trigger financial statements sync."""
    asyncio.create_task(sync_all_async())
    return {"status": "accepted", "message": "Statements sync started"}


@router.post("/listings")
async def trigger_listings_sync():
    """Trigger stock listings sync."""
    asyncio.create_task(sync_all_async())
    return {"status": "accepted", "message": "Listings sync started"}


@router.post("/all")
async def trigger_all_sync():
    """Trigger full data sync (listings → quotes → statements → metrics)."""
    asyncio.create_task(sync_all_async())
    return {"status": "accepted", "message": "Full sync started"}


@router.get("/status")
def get_status(db: Session = Depends(get_db)):
    """Get current sync status (polled every 5 seconds by frontend)."""
    return get_sync_status(db)

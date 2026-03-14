"""Bulk import script for initial data load from J-Quants API."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import date, timedelta
from backend.database import SessionLocal
from backend.services.jquants_client import JQuantsClient
from backend.services.sync_service import sync_listings, sync_quotes, sync_statements
from backend.services.metrics_service import batch_calculate


def main():
    print("Starting bulk import...")
    db = SessionLocal()

    try:
        client = JQuantsClient()

        # Step 1: Listings
        print("[1/4] Syncing stock listings...")
        count = sync_listings(db, client)
        print(f"  → {count} stocks synced")

        # Step 2: Quotes (5 years)
        to_date = date.today()
        from_date = to_date - timedelta(days=365 * 5)
        print(f"[2/4] Syncing daily quotes ({from_date} to {to_date})...")
        count = sync_quotes(db, client, from_date, to_date)
        print(f"  → {count} quote records synced")

        # Step 3: Financial statements
        print(f"[3/4] Syncing financial statements ({from_date} to {to_date})...")
        count = sync_statements(db, client, from_date, to_date)
        print(f"  → {count} financial records synced")

        # Step 4: Calculate metrics
        print("[4/4] Calculating metrics...")
        batch_calculate(db)
        print("  → Metrics calculated")

        print("\nBulk import completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

"""Database initialization script — creates all tables."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database import engine, Base
from backend.models import *  # noqa: F401, F403 — import all models to register them


def main():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Done. Database initialized successfully.")


if __name__ == "__main__":
    main()

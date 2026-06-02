"""Seed the database with rich test data for all entities.

Usage:
    python scripts/seed.py            # Append data
    python scripts/seed.py --clean    # Delete all existing data first
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlmodel import Session

from app.database import engine
from app.seeder import seed_database


def seed():
    clean = "--clean" in sys.argv
    with Session(engine) as session:
        seed_database(session, clean=clean)
        session.commit()

    print("✅ Seed completed successfully!")
    print("   Owners: 2")
    print("   Properties: 2")
    print("   Units: 3")
    print("   Tenants: 2")
    print("   Leases: 2 (1 active with IPC update, 1 active local)")
    print("   Rent conditions: 3")
    print("   Tax profiles: 2")
    print("   Deposits: 2")
    print("   Index updates: 1")
    print("   Invoices: 6 (2 paid, 1 partial, 3 draft)")
    print("   Payments: 3")
    print("   Expenses: 8")
    print("   Bank movements: 3 (all unmatched)")


if __name__ == "__main__":
    seed()

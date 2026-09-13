"""Seed the database with demo data.

Usage:
    python scripts/seed.py                    # Dataset básico
    python scripts/seed.py --full             # Dataset completo de exploración
    python scripts/seed.py --clean            # Borra todo antes de sembrar
    python scripts/seed.py --full --years 3 --seed 42
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlmodel import Session

from app.database import engine
from app.seeder import DEMO_DEFAULT_SEED, seed_database, seed_demo_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Carga datos de demostración")
    parser.add_argument(
        "--full",
        action="store_true",
        help="Genera el dataset completo (fechas relativas a hoy)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Elimina todos los datos existentes antes de sembrar",
    )
    parser.add_argument(
        "--years",
        type=int,
        default=3,
        help="Años de histórico con --full (por defecto 3)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEMO_DEFAULT_SEED,
        help="Semilla aleatoria para reproducibilidad con --full",
    )
    args = parser.parse_args()

    with Session(engine) as session:
        if args.full:
            summary = seed_demo_dataset(
                session,
                clean=args.clean,
                years=args.years,
                seed=args.seed,
            )
            session.commit()
            if not summary:
                print("⚠️  Ya hay datos. Usa --clean para regenerar el dataset.")
                return
            print("✅ Dataset completo generado:")
            for key, value in summary.items():
                print(f"   {key}: {value}")
            return

        inserted = seed_database(session, clean=args.clean)
        session.commit()
        if not inserted:
            print("⚠️  Ya hay datos. Usa --clean para regenerar el seed.")
            return
        print("✅ Seed básico completado:")
        print("   Owners: 2 · Properties: 2 · Units: 3 · Tenants: 2")
        print("   Leases: 2 · Invoices: 6 · Payments: 3 · Expenses: 8")
        print("   Bank movements: 3")


if __name__ == "__main__":
    main()

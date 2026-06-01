"""Seed the database with rich test data for all entities.

Usage:
    python scripts/seed.py            # Append data
    python scripts/seed.py --clean    # Delete all existing data first
"""

import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlmodel import Session

from app.database import engine
from app.models.bank import BankMovement, Reconciliation
from app.models.expense import Expense
from app.models.invoice import Invoice, InvoiceLine
from app.models.lease import Deposit, IndexUpdate, Lease, RentCondition, TaxProfile
from app.models.owner import Owner
from app.models.payment import Payment
from app.models.property import Property
from app.models.tenant import Tenant
from app.models.unit import Unit


def seed():
    if "--clean" in sys.argv:
        print("🧹 Cleaning existing data...")
        with Session(engine) as s:
            for table in (
                Reconciliation, BankMovement,
                Payment, InvoiceLine, Invoice,
                Expense, IndexUpdate, Deposit, TaxProfile, RentCondition,
                Lease, Unit, Property, Tenant, Owner,
            ):
                s.exec(table.__table__.delete())
            s.commit()
        print("   Done.\n")

    with Session(engine) as session:
        # ── Owners ──────────────────────────────────────────────
        owner1 = Owner(
            name="María García López",
            document_type="DNI",
            document_number="12345678A",
            email="maria@example.com",
            phone="+34 611 111 111",
            address="Calle Mayor 10, Madrid",
        )
        owner2 = Owner(
            name="Carlos Martínez Ruiz",
            document_type="DNI",
            document_number="87654321B",
            email="carlos@example.com",
            phone="+34 622 222 222",
            address="Av. Mediterráneo 25, Valencia",
        )
        session.add_all([owner1, owner2])
        session.flush()

        # ── Properties ──────────────────────────────────────────
        prop1 = Property(
            name="Piso Centro",
            address="Calle Gran Vía 42, 3ºB",
            city="Madrid",
            province="Madrid",
            zip_code="28013",
            cadastral_ref="1234567VK1234A",
            owner_id=owner1.id,
        )
        prop2 = Property(
            name="Local Comercial",
            address="Av. del Puerto 18, Local 5",
            city="Valencia",
            province="Valencia",
            zip_code="46021",
            cadastral_ref="7654321VK5678B",
            owner_id=owner2.id,
        )
        session.add_all([prop1, prop2])
        session.flush()

        # ── Units ───────────────────────────────────────────────
        unit1 = Unit(
            property_id=prop1.id,
            name="Vivienda 3ºB",
            unit_type="vivienda",
            area_m2=85.0,
            is_active=True,
        )
        unit2 = Unit(
            property_id=prop1.id,
            name="Garaje 42",
            unit_type="garage",
            area_m2=12.0,
            is_active=True,
        )
        unit3 = Unit(
            property_id=prop2.id,
            name="Local 5",
            unit_type="local",
            area_m2=120.0,
            is_active=True,
        )
        session.add_all([unit1, unit2, unit3])
        session.flush()

        # ── Tenants ─────────────────────────────────────────────
        tenant1 = Tenant(
            name="Ana Fernández Pérez",
            document_type="DNI",
            document_number="11111111C",
            email="ana@example.com",
            phone="+34 633 333 333",
        )
        tenant2 = Tenant(
            name="Javier Gómez Sánchez",
            document_type="NIE",
            document_number="Y2222222D",
            email="javier@example.com",
            phone="+34 644 444 444",
        )
        session.add_all([tenant1, tenant2])
        session.flush()

        # ── Leases ──────────────────────────────────────────────
        lease1 = Lease(
            unit_id=unit1.id,
            tenant_id=tenant1.id,
            owner_id=owner1.id,
            start_date=date(2024, 1, 1),
            end_date=date(2026, 12, 31),
            is_active=True,
            notes="Contrato vivienda centro. Actualización IPC anual.",
        )
        lease2 = Lease(
            unit_id=unit3.id,
            tenant_id=tenant2.id,
            owner_id=owner2.id,
            start_date=date(2023, 6, 1),
            end_date=None,
            is_active=True,
            notes="Alquiler local comercial. Sin fecha fin.",
        )
        session.add_all([lease1, lease2])
        session.flush()

        # ── Rent Conditions ─────────────────────────────────────
        rc1 = RentCondition(
            lease_id=lease1.id,
            start_date=date(2024, 1, 1),
            monthly_rent=Decimal("950.00"),
            notes="Renta inicial",
        )
        rc2 = RentCondition(
            lease_id=lease1.id,
            start_date=date(2025, 1, 1),
            monthly_rent=Decimal("978.50"),
            notes="Actualización IPC 2025 (3%)",
        )
        rc3 = RentCondition(
            lease_id=lease2.id,
            start_date=date(2023, 6, 1),
            monthly_rent=Decimal("1800.00"),
            notes="Renta inicial local",
        )
        session.add_all([rc1, rc2, rc3])
        session.flush()

        # ── Index Updates ───────────────────────────────────────
        iu1 = IndexUpdate(
            lease_id=lease1.id,
            application_date=date(2025, 1, 1),
            previous_rent=Decimal("950.00"),
            new_rent=Decimal("978.50"),
            index_rate=Decimal("0.03"),
            index_name="IPC",
            notes="IPC 2024 publicado por INE",
        )
        session.add(iu1)
        session.flush()

        # ── Tax Profiles ────────────────────────────────────────
        tp1 = TaxProfile(
            lease_id=lease1.id,
            vat_rate=Decimal("10.00"),
            irpf_rate=Decimal("19.00"),
            vat_exempt=False,
            withholding_applies=True,
        )
        tp2 = TaxProfile(
            lease_id=lease2.id,
            vat_rate=Decimal("21.00"),
            irpf_rate=Decimal("0.00"),
            vat_exempt=False,
            withholding_applies=False,
        )
        session.add_all([tp1, tp2])
        session.flush()

        # ── Deposits ────────────────────────────────────────────
        dep1 = Deposit(
            lease_id=lease1.id,
            amount=Decimal("950.00"),
            deposit_date=date(2024, 1, 1),
            agency="IVIMA",
        )
        dep2 = Deposit(
            lease_id=lease2.id,
            amount=Decimal("3600.00"),
            deposit_date=date(2023, 6, 1),
            agency="IVIMA",
        )
        session.add_all([dep1, dep2])
        session.flush()

        # ── Invoices (generadas manualmente para el seed) ──────
        invoices_data = [
            # lease1 — últimos 3 meses
            {"period": "2026-03", "issue": date(2026, 3, 1), "base": "950.00", "status": "paid"},
            {"period": "2026-04", "issue": date(2026, 4, 1), "base": "978.50", "status": "paid"},
            {"period": "2026-05", "issue": date(2026, 5, 1), "base": "978.50", "status": "draft"},
            # lease2 — últimos 3 meses
            {"period": "2026-03", "issue": date(2026, 3, 1), "base": "1800.00", "status": "paid"},
            {"period": "2026-04", "issue": date(2026, 4, 1), "base": "1800.00", "status": "partial"},
            {"period": "2026-05", "issue": date(2026, 5, 1), "base": "1800.00", "status": "draft"},
        ]

        leases_for_invoices = [lease1, lease1, lease1, lease2, lease2, lease2]
        tax_profiles = [tp1, tp1, tp1, tp2, tp2, tp2]

        for i, inv_data in enumerate(invoices_data):
            base = Decimal(inv_data["base"])
            tp = tax_profiles[i]
            vat = base * tp.vat_rate / Decimal("100")
            irpf = base * tp.irpf_rate / Decimal("100")
            total = base + vat - irpf

            inv = Invoice(
                period=inv_data["period"],
                lease_id=leases_for_invoices[i].id,
                issue_date=inv_data["issue"],
                status=inv_data["status"],
                total_base=base,
                total_vat=vat,
                total_irpf_withholding=irpf,
                total=total,
            )
            session.add(inv)
            session.flush()

            line = InvoiceLine(
                invoice_id=inv.id,
                concept=f"Alquiler {inv_data['period']}",
                base_amount=base,
                vat_rate=tp.vat_rate,
                vat_amount=vat,
                irpf_rate=tp.irpf_rate,
                irpf_withholding=irpf,
            )
            session.add(line)

            # ── Payments ────────────────────────────────────────
            if inv_data["status"] == "paid":
                session.add(Payment(
                    invoice_id=inv.id,
                    amount=total,
                    payment_date=inv_data["issue"] + timedelta(days=5),
                    method="transferencia",
                ))
            elif inv_data["status"] == "partial":
                half = total / Decimal("2")
                session.add(Payment(
                    invoice_id=inv.id,
                    amount=half,
                    payment_date=inv_data["issue"] + timedelta(days=5),
                    method="transferencia",
                    notes="Pago parcial",
                ))

        session.flush()

        # ── Expenses ────────────────────────────────────────────
        expenses_data = [
            # prop1 expenses
            {"property_id": prop1.id, "category": "community", "amount": "85.00", "date": date(2026, 1, 5), "deductible": True, "supplier": "Comunidad Gran Vía"},
            {"property_id": prop1.id, "category": "insurance", "amount": "35.50", "date": date(2026, 2, 10), "deductible": True, "supplier": "Mapfre"},
            {"property_id": prop1.id, "category": "repairs", "amount": "240.00", "date": date(2026, 3, 15), "deductible": True, "supplier": "Fontanero Express"},
            {"property_id": prop1.id, "category": "supplies", "amount": "60.00", "date": date(2026, 4, 1), "deductible": False, "supplier": "Iberdrola"},
            # prop2 expenses
            {"property_id": prop2.id, "category": "taxes", "amount": "450.00", "date": date(2026, 4, 20), "deductible": True, "supplier": "Ayuntamiento Valencia"},
            {"property_id": prop2.id, "category": "admin_fees", "amount": "120.00", "date": date(2026, 3, 1), "deductible": True, "supplier": "Gestoría López"},
            {"property_id": prop2.id, "category": "insurance", "amount": "85.00", "date": date(2026, 1, 15), "deductible": True, "supplier": "Allianz"},
            {"property_id": prop2.id, "category": "repairs", "amount": "680.00", "date": date(2026, 5, 10), "deductible": True, "supplier": "Electricidad Valencia SL"},
        ]
        for exp in expenses_data:
            session.add(Expense(
                property_id=exp["property_id"],
                category=exp["category"],
                amount=Decimal(exp["amount"]),
                expense_date=exp["date"],
                deductible=exp["deductible"],
                supplier=exp["supplier"],
                notes=None,
            ))
        session.flush()

        # ── Bank Movements (for reconciliation) ────────────────
        bank_movements = [
            BankMovement(
                entry_date=date(2026, 5, 6),
                value_date=date(2026, 5, 5),
                amount=Decimal("978.50"),
                concept="TRANSFERENCIA ANA FERNANDEZ PEREZ ALQUILER MAYO",
                iban_origin="ES9121000418450200051332",
                reference="REF12345",
                status="unmatched",
            ),
            BankMovement(
                entry_date=date(2026, 5, 7),
                value_date=date(2026, 5, 6),
                amount=Decimal("1800.00"),
                concept="INGRESO NOMINA JAVIER GOMEZ",
                iban_origin="ES6621000418401234567891",
                reference="REF12346",
                status="unmatched",
            ),
            BankMovement(
                entry_date=date(2026, 4, 15),
                value_date=date(2026, 4, 14),
                amount=Decimal("35.50"),
                concept="SEGURO MAPFRE RECIBO MENSUAL",
                iban_origin=None,
                reference=None,
                status="unmatched",
            ),
        ]
        session.add_all(bank_movements)
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

"""Reusable seed logic: inserts sample data for development/demo."""

import random
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

from sqlmodel import Session, func, select

from app.config import INVOICE_PAYMENT_TERMS_DAYS
from app.models.bank import BankMovement, Reconciliation
from app.models.event_log import EventLog
from app.models.expense import Expense
from app.models.invoice import Invoice, InvoiceLine
from app.models.lease import Deposit, IndexUpdate, Lease, RentCondition, TaxProfile
from app.models.owner import Owner
from app.models.payment import Payment
from app.models.property import Property
from app.models.tenant import Tenant
from app.models.unit import Unit
from app.services.invoice_numbering_service import InvoiceNumberingService
from app.services.invoice_service import InvoiceService
from app.services.payment_service import PaymentService

DEMO_DEFAULT_SEED = 20260913


def _wipe_all(session: Session) -> None:
    """Delete every business table in foreign-key safe order."""
    for table in (Reconciliation, Payment, InvoiceLine):
        session.exec(table.__table__.delete())
    session.exec(
        Invoice.__table__.delete().where(Invoice.__table__.c.corrected_invoice_id.is_not(None))
    )
    for table in (
        Invoice,
        Expense,
        IndexUpdate,
        Deposit,
        TaxProfile,
        RentCondition,
        Lease,
        Unit,
        Property,
        Tenant,
        Owner,
        BankMovement,
        EventLog,
    ):
        session.exec(table.__table__.delete())
    session.flush()


def seed_database(session: Session, *, clean: bool = False) -> bool:
    """Insert sample data into an empty database.

    Args:
        session: SQLModel Session bound to the target database.
        clean: If True, delete all existing data before seeding.

    Returns:
        True if any data was inserted, False if nothing was done
        (because data already existed and clean was False).
    """

    if clean:
        _wipe_all(session)

    if not clean and session.exec(select(Owner)).first() is not None:
        return False

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

    # ── Invoices ────────────────────────────────────────────
    invoices_data = [
        {"period": "2026-03", "issue": date(2026, 3, 1), "base": "950.00", "status": "paid"},
        {"period": "2026-04", "issue": date(2026, 4, 1), "base": "978.50", "status": "paid"},
        {"period": "2026-05", "issue": date(2026, 5, 1), "base": "978.50", "status": "draft"},
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

        if inv_data["status"] == "paid":
            session.add(
                Payment(
                    invoice_id=inv.id,
                    amount=total,
                    payment_date=inv_data["issue"] + timedelta(days=5),
                    method="transferencia",
                )
            )
        elif inv_data["status"] == "partial":
            half = total / Decimal("2")
            session.add(
                Payment(
                    invoice_id=inv.id,
                    amount=half,
                    payment_date=inv_data["issue"] + timedelta(days=5),
                    method="transferencia",
                    notes="Pago parcial",
                )
            )

    session.flush()

    # ── Expenses ────────────────────────────────────────────
    expenses_data = [
        {
            "property_id": prop1.id,
            "category": "community",
            "amount": "85.00",
            "date": date(2026, 1, 5),
            "deductible": True,
            "supplier": "Comunidad Gran Vía",
        },
        {
            "property_id": prop1.id,
            "category": "insurance",
            "amount": "35.50",
            "date": date(2026, 2, 10),
            "deductible": True,
            "supplier": "Mapfre",
        },
        {
            "property_id": prop1.id,
            "category": "repairs",
            "amount": "240.00",
            "date": date(2026, 3, 15),
            "deductible": True,
            "supplier": "Fontanero Express",
        },
        {
            "property_id": prop1.id,
            "category": "supplies",
            "amount": "60.00",
            "date": date(2026, 4, 1),
            "deductible": False,
            "supplier": "Iberdrola",
        },
        {
            "property_id": prop2.id,
            "category": "taxes",
            "amount": "450.00",
            "date": date(2026, 4, 20),
            "deductible": True,
            "supplier": "Ayuntamiento Valencia",
        },
        {
            "property_id": prop2.id,
            "category": "admin_fees",
            "amount": "120.00",
            "date": date(2026, 3, 1),
            "deductible": True,
            "supplier": "Gestoría López",
        },
        {
            "property_id": prop2.id,
            "category": "insurance",
            "amount": "85.00",
            "date": date(2026, 1, 15),
            "deductible": True,
            "supplier": "Allianz",
        },
        {
            "property_id": prop2.id,
            "category": "repairs",
            "amount": "680.00",
            "date": date(2026, 5, 10),
            "deductible": True,
            "supplier": "Electricidad Valencia SL",
        },
    ]
    for exp in expenses_data:
        session.add(
            Expense(
                property_id=exp["property_id"],
                category=exp["category"],
                amount=Decimal(exp["amount"]),
                expense_date=exp["date"],
                deductible=exp["deductible"],
                supplier=exp["supplier"],
                notes=None,
            )
        )
    session.flush()

    # ── Bank Movements ──────────────────────────────────────
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

    return True


# ── Demo dataset (relative to today) ────────────────────────────────────────

_DEMO_OWNERS = [
    (
        "María García López",
        "DNI",
        "12345678A",
        "maria.garcia@example.com",
        "+34 611 111 111",
        "Calle Mayor 10, 28013 Madrid",
    ),
    (
        "Carlos Martínez Ruiz",
        "DNI",
        "87654321B",
        "carlos.martinez@example.com",
        "+34 622 222 222",
        "Av. del Puerto 18, 46021 Valencia",
    ),
    (
        "Lucía Fernández Ortega",
        "DNI",
        "45678912C",
        "lucia.fernandez@example.com",
        "+34 633 333 333",
        "Calle Betis 4, 41010 Sevilla",
    ),
    (
        "Antonio Rodríguez Vega",
        "DNI",
        "23456789D",
        "antonio.rodriguez@example.com",
        "+34 644 444 444",
        "Gran Vía 8, 48001 Bilbao",
    ),
    (
        "Carmen Sánchez Molina",
        "DNI",
        "56789123E",
        "carmen.sanchez@example.com",
        "+34 655 555 555",
        "Alameda Principal 12, 29005 Málaga",
    ),
]

_DEMO_PROPERTIES = [
    ("Piso Gran Vía", "Calle Gran Vía 42, 3ºB", "Madrid", "Madrid", "28013", "1234567VK1234A", 0),
    ("Piso Malasaña", "Calle Pez 17, 2ºA", "Madrid", "Madrid", "28004", "2345678VK2345B", 0),
    (
        "Local Puerto",
        "Av. del Puerto 18, Local 5",
        "Valencia",
        "Valencia",
        "46021",
        "3456789VK3456C",
        1,
    ),
    ("Piso Ruzafa", "Calle Cádiz 55, 4ºC", "Valencia", "Valencia", "46006", "4567890VK4567D", 1),
    ("Piso Triana", "Calle Betis 4, 1ºB", "Sevilla", "Sevilla", "41010", "5678901VK5678E", 2),
    (
        "Local Nervión",
        "Av. Eduardo Dato 23, Local 3",
        "Sevilla",
        "Sevilla",
        "41005",
        "6789012VK6789F",
        2,
    ),
    (
        "Piso Indautxu",
        "Calle Licenciado Poza 30, 5ºD",
        "Bilbao",
        "Bizkaia",
        "48011",
        "7890123VK7890G",
        3,
    ),
    (
        "Piso Centro Histórico",
        "Calle Larios 8, Ático",
        "Málaga",
        "Málaga",
        "29015",
        "8901234VK8901H",
        4,
    ),
]

_DEMO_UNITS = [
    (0, "Vivienda 3ºB", "vivienda", 85.0),
    (0, "Garaje 42", "garage", 12.0),
    (1, "Vivienda 2ºA", "vivienda", 72.0),
    (1, "Garaje 12", "garage", 11.0),
    (2, "Local 5", "local", 120.0),
    (3, "Vivienda 4ºC", "vivienda", 95.0),
    (3, "Trastero 7", "trastero", 6.0),
    (4, "Vivienda 1ºB", "vivienda", 78.0),
    (5, "Local 3", "local", 150.0),
    (6, "Vivienda 5ºD", "vivienda", 90.0),
    (7, "Vivienda Ático", "vivienda", 110.0),
    (7, "Plaza garaje 3", "garage", 14.0),
]

_DEMO_TENANTS = [
    ("Ana Fernández Pérez", "DNI", "11111111C", "ana.fernandez@example.com", "+34 611 222 333"),
    ("Javier Gómez Sánchez", "NIE", "Y2222222D", "javier.gomez@example.com", "+34 622 333 444"),
    (
        "Distribuciones Levante SL",
        "CIF",
        "B12345678",
        "admin@distlevante.example.com",
        "+34 963 111 222",
    ),
    ("Marta López Ruiz", "DNI", "33333333E", "marta.lopez@example.com", "+34 633 444 555"),
    ("Pablo Hernández Gil", "DNI", "44444444F", "pablo.hernandez@example.com", "+34 644 555 666"),
    ("Elena Navarro Castro", "DNI", "55555555G", "elena.navarro@example.com", "+34 655 666 777"),
    (
        "Restauración Nervión SL",
        "CIF",
        "B87654321",
        "gerencia@restnervion.example.com",
        "+34 954 222 333",
    ),
    ("Sergio Romero Díaz", "DNI", "66666666H", "sergio.romero@example.com", "+34 666 777 888"),
    ("Laura Vidal Peña", "DNI", "77777777J", "laura.vidal@example.com", "+34 677 888 999"),
    ("Andrés Molina Torres", "NIE", "X8888888K", "andres.molina@example.com", "+34 688 999 000"),
    ("Nuria Cano Serrano", "DNI", "99999999L", "nuria.cano@example.com", "+34 699 000 111"),
]

_DEMO_LEASES: list[dict] = [
    {
        "unit": 0,
        "tenant": 0,
        "owner": 0,
        "start": 36,
        "end": None,
        "rent": "950.00",
        "vat_rate": "0.00",
        "irpf_rate": "19.00",
        "vat_exempt": True,
        "withholding": True,
        "deposit": "950.00",
        "agency": "IVIMA",
        "revisions": [(12, "0.03", "IPC"), (24, "0.03", "IPC")],
        "notes": "Vivienda habitual. Renta actualizada con el IPC.",
    },
    {
        "unit": 1,
        "tenant": 0,
        "owner": 0,
        "start": 36,
        "end": None,
        "rent": "60.00",
        "vat_rate": "21.00",
        "irpf_rate": "0.00",
        "vat_exempt": False,
        "withholding": False,
        "deposit": "120.00",
        "agency": "IVIMA",
        "revisions": [],
        "notes": "Alquiler de plaza de garaje.",
    },
    {
        "unit": 2,
        "tenant": 1,
        "owner": 0,
        "start": 30,
        "end": None,
        "rent": "875.00",
        "vat_rate": "10.00",
        "irpf_rate": "19.00",
        "vat_exempt": False,
        "withholding": True,
        "deposit": "875.00",
        "agency": "IVIMA",
        "revisions": [(12, "0.03", "IPC")],
        "notes": "Vivienda con IVA reducido y retención de IRPF.",
    },
    {
        "unit": 4,
        "tenant": 2,
        "owner": 1,
        "start": 36,
        "end": None,
        "rent": "1800.00",
        "vat_rate": "21.00",
        "irpf_rate": "0.00",
        "vat_exempt": False,
        "withholding": False,
        "deposit": "3600.00",
        "agency": "IVIMA",
        "revisions": [(12, "0.03", "IPC"), (24, "0.035", "IPC")],
        "notes": "Local comercial de distribución.",
    },
    {
        "unit": 5,
        "tenant": 3,
        "owner": 1,
        "start": 24,
        "end": None,
        "rent": "800.00",
        "vat_rate": "0.00",
        "irpf_rate": "19.00",
        "vat_exempt": True,
        "withholding": True,
        "deposit": "800.00",
        "agency": "Generalitat Valenciana",
        "revisions": [(12, "0.03", "IPC")],
        "notes": "Vivienda habitual, exenta de IVA.",
    },
    {
        "unit": 6,
        "tenant": 3,
        "owner": 1,
        "start": 24,
        "end": None,
        "rent": "45.00",
        "vat_rate": "21.00",
        "irpf_rate": "0.00",
        "vat_exempt": False,
        "withholding": False,
        "deposit": "90.00",
        "agency": "Generalitat Valenciana",
        "revisions": [],
        "notes": "Trastero vinculado a la vivienda 4ºC.",
    },
    {
        "unit": 7,
        "tenant": 4,
        "owner": 2,
        "start": 36,
        "end": 6,
        "rent": "720.00",
        "vat_rate": "0.00",
        "irpf_rate": "19.00",
        "vat_exempt": True,
        "withholding": True,
        "deposit": "720.00",
        "agency": "AGA",
        "deposit_returned": True,
        "revisions": [(12, "0.03", "IPC"), (24, "0.03", "IPC")],
        "notes": "Contrato finalizado: el inquilino no renovó.",
    },
    {
        "unit": 7,
        "tenant": 5,
        "owner": 2,
        "start": 5,
        "end": None,
        "rent": "760.00",
        "vat_rate": "0.00",
        "irpf_rate": "19.00",
        "vat_exempt": True,
        "withholding": True,
        "deposit": "760.00",
        "agency": "AGA",
        "revisions": [],
        "notes": "Nuevo contrato tras la salida del anterior inquilino.",
    },
    {
        "unit": 8,
        "tenant": 6,
        "owner": 2,
        "start": 24,
        "end": None,
        "rent": "2200.00",
        "vat_rate": "21.00",
        "irpf_rate": "0.00",
        "vat_exempt": False,
        "withholding": False,
        "deposit": "4400.00",
        "agency": "AGA",
        "revisions": [(12, "0.03", "IPC")],
        "notes": "Restaurante. Fianza de dos mensualidades.",
    },
    {
        "unit": 9,
        "tenant": 7,
        "owner": 3,
        "start": 18,
        "end": None,
        "rent": "900.00",
        "vat_rate": None,
        "irpf_rate": None,
        "vat_exempt": False,
        "withholding": False,
        "deposit": "900.00",
        "agency": "Etxebide",
        "revisions": [],
        "notes": "Pendiente configurar el perfil fiscal del contrato.",
    },
    {
        "unit": 10,
        "tenant": 8,
        "owner": 4,
        "start": 12,
        "end": None,
        "rent": "1050.00",
        "vat_rate": "0.00",
        "irpf_rate": "19.00",
        "vat_exempt": True,
        "withholding": True,
        "deposit": "1050.00",
        "agency": "Agencia Municipal de Málaga",
        "revisions": [(6, "0.025", "IRAV")],
        "notes": "Actualización con el nuevo índice IRAV.",
    },
    {
        "unit": 11,
        "tenant": 9,
        "owner": 4,
        "start": 8,
        "end": None,
        "rent": "70.00",
        "vat_rate": "21.00",
        "irpf_rate": "0.00",
        "vat_exempt": False,
        "withholding": False,
        "deposit": "140.00",
        "agency": "Agencia Municipal de Málaga",
        "revisions": [],
        "notes": "Plaza de garaje en el mismo edificio.",
    },
    {
        "unit": 3,
        "tenant": 10,
        "owner": 1,
        "start": 3,
        "end": None,
        "rent": "55.00",
        "vat_rate": "21.00",
        "irpf_rate": "0.00",
        "vat_exempt": False,
        "withholding": False,
        "deposit": "110.00",
        "agency": "Generalitat Valenciana",
        "revisions": [],
        "notes": "Garaje alquilado por separado.",
    },
]

_DEMO_FORCED_PARTIAL = {(0, 1), (3, 2), (8, 3)}
_DEMO_FORCED_UNPAID = {(2, 4)}
_DEMO_RECTIFY = (3, 6)

_DEMO_IBANS = [
    "ES9121000418450200051332",
    "ES6621000418401234567891",
    "ES7100302053091234567895",
    "ES1000492352082414205416",
    "ES9420805801101234567891",
    "ES6000491500051234567892",
]

_DEMO_EXPENSE_TEMPLATES = [
    ("community", 5500, 13000),
    ("repairs", 8000, 65000),
    ("supplies", 3500, 16000),
    ("taxes", 11000, 58000),
    ("insurance", 2500, 14000),
    ("admin_fees", 6000, 22000),
]

_DEMO_SUPPLIERS = {
    "community": ["Comunidad de Propietarios", "Administración de Fincas"],
    "repairs": ["Fontanería Express", "Electricidad del Sur", "Reformas Ibéricas"],
    "supplies": ["Iberdrola", "Naturgy", "Aguas Municipales"],
    "taxes": ["Ayuntamiento", "Agencia Tributaria"],
    "insurance": ["Mapfre", "Allianz", "Mutua Madrileña"],
    "admin_fees": ["Gestoría López", "Asesoría Nova", "Gestión Fiscal SL"],
}

_DEMO_OTHER_MOVEMENTS = [
    (9, "35.50", "RECIBO SEGURO MAPFRE POLIZA HOGAR"),
    (14, "118.40", "ADEUDO IBERDROLA SUMINISTRO ELECTRICO"),
    (23, "12.00", "COMISION MANTENIMIENTO CUENTA"),
    (31, "450.00", "TRANSFERENCIA RECIBIDA COMUNIDAD DE PROPIETARIOS"),
    (45, "240.00", "RECIBO GESTORIA FISCAL TRIMESTRE"),
    (62, "980.00", "INGRESO EFECTIVO OFICINA"),
]


def _month_start(value: date) -> date:
    return value.replace(day=1)


def _shift_months(value: date, months: int) -> date:
    index = value.month - 1 + months
    return date(value.year + index // 12, index % 12 + 1, 1)


def _month_end(value: date) -> date:
    return _shift_months(value, 1) - timedelta(days=1)


def _period(value: date) -> str:
    return f"{value.year}-{value.month:02d}"


def _iter_months(start: date, end: date) -> list[date]:
    months: list[date] = []
    cursor = start
    while cursor <= end:
        months.append(cursor)
        cursor = _shift_months(cursor, 1)
    return months


def _rent_at(schedule: list[tuple[date, Decimal]], target: date) -> Decimal:
    rent = schedule[0][1]
    for effective, amount in schedule:
        if effective <= target:
            rent = amount
        else:
            break
    return rent


def _payment_plan(rng: random.Random, months_ago: int, key: tuple[int, int]) -> str:
    if key in _DEMO_FORCED_PARTIAL:
        return "partial"
    if key in _DEMO_FORCED_UNPAID:
        return "unpaid"
    roll = rng.random()
    if months_ago == 0:
        return "paid" if roll < 0.45 else "partial" if roll < 0.7 else "unpaid"
    if months_ago == 1:
        return "paid" if roll < 0.75 else "partial" if roll < 0.9 else "unpaid"
    return "paid" if roll < 0.94 else "partial" if roll < 0.99 else "unpaid"


def _payment_method(rng: random.Random, unit_type: str) -> str:
    if unit_type == "local":
        return "transferencia"
    if unit_type in ("garage", "trastero"):
        return rng.choice(["transferencia", "efectivo"])
    return rng.choice(["transferencia", "transferencia", "domiciliacion", "tarjeta"])


def _snapshot_parties(invoice: Invoice, lease: Lease) -> None:
    if lease.owner is not None:
        invoice.issuer_name = lease.owner.name
        invoice.issuer_document_type = lease.owner.document_type
        invoice.issuer_document_number = lease.owner.document_number
        invoice.issuer_address = lease.owner.address
    if lease.tenant is not None:
        invoice.recipient_name = lease.tenant.name
        invoice.recipient_document_type = lease.tenant.document_type
        invoice.recipient_document_number = lease.tenant.document_number
        invoice.recipient_address = lease.tenant.address


def _row_count(session: Session, model: type) -> int:
    return int(session.exec(select(func.count()).select_from(model)).one())


def seed_demo_dataset(
    session: Session,
    *,
    clean: bool = False,
    years: int = 3,
    seed: int = DEMO_DEFAULT_SEED,
) -> dict[str, int]:
    """Genera un dataset de demostración completo con fechas relativas a hoy.

    Args:
        session: SQLModel Session bound to the target database.
        clean: If True, delete all existing data before seeding.
        years: Months of history are derived from this many years.
        seed: Random seed for reproducible datasets.

    Returns:
        A summary of row counts per entity, or ``{}`` when the database
        already contains data and ``clean`` is False.
    """

    if clean:
        _wipe_all(session)

    if session.exec(select(Owner)).first() is not None:
        return {}

    rng = random.Random(seed)
    today = date.today()
    current_month = _month_start(today)
    horizon_start = _shift_months(current_month, -12 * max(years, 1))

    owners = [
        Owner(
            name=name,
            document_type=doc_type,
            document_number=doc_number,
            email=email,
            phone=phone,
            address=address,
        )
        for name, doc_type, doc_number, email, phone, address in _DEMO_OWNERS
    ]
    session.add_all(owners)
    session.flush()

    properties = [
        Property(
            name=name,
            address=address,
            city=city,
            province=province,
            zip_code=zip_code,
            cadastral_ref=cadastral_ref,
            owner_id=owners[owner_index].id,
        )
        for name, address, city, province, zip_code, cadastral_ref, owner_index in _DEMO_PROPERTIES
    ]
    session.add_all(properties)
    session.flush()

    units = [
        Unit(
            property_id=properties[property_index].id,
            name=name,
            unit_type=unit_type,
            area_m2=area,
            is_active=True,
        )
        for property_index, name, unit_type, area in _DEMO_UNITS
    ]
    session.add_all(units)
    session.flush()

    tenants = [
        Tenant(
            name=name,
            document_type=doc_type,
            document_number=doc_number,
            email=email,
            phone=phone,
        )
        for name, doc_type, doc_number, email, phone in _DEMO_TENANTS
    ]
    session.add_all(tenants)
    session.flush()

    leases: list[Lease] = []
    for cfg in _DEMO_LEASES:
        start = _shift_months(current_month, -int(cfg["start"]))
        end = _month_end(_shift_months(current_month, -int(cfg["end"]))) if cfg["end"] else None
        leases.append(
            Lease(
                unit_id=units[int(cfg["unit"])].id,
                tenant_id=tenants[int(cfg["tenant"])].id,
                owner_id=owners[int(cfg["owner"])].id,
                start_date=start,
                end_date=end,
                is_active=end is None,
                notes=str(cfg["notes"]),
            )
        )
    session.add_all(leases)
    session.flush()

    rent_schedules: list[list[tuple[date, Decimal]]] = []
    for cfg, lease in zip(_DEMO_LEASES, leases):
        base = Decimal(str(cfg["rent"]))
        schedule: list[tuple[date, Decimal]] = [(lease.start_date, base)]
        current_rent = base
        for months_after, rate, index_name in cfg["revisions"]:
            effective = _shift_months(lease.start_date, int(months_after))
            previous_rent = current_rent
            current_rent = (current_rent * (Decimal("1") + Decimal(str(rate)))).quantize(
                Decimal("0.01")
            )
            session.add(
                IndexUpdate(
                    lease_id=lease.id,
                    application_date=effective,
                    previous_rent=previous_rent,
                    new_rent=current_rent,
                    index_rate=Decimal(str(rate)),
                    index_name=str(index_name),
                    notes=f"Actualización {index_name} tras {months_after} meses",
                )
            )
            schedule.append((effective, current_rent))
        rent_schedules.append(schedule)

        for position, (effective, amount) in enumerate(schedule):
            session.add(
                RentCondition(
                    lease_id=lease.id,
                    start_date=effective,
                    monthly_rent=amount,
                    notes="Renta inicial" if position == 0 else "Actualización de renta",
                )
            )

        if cfg["vat_rate"] is not None:
            session.add(
                TaxProfile(
                    lease_id=lease.id,
                    vat_rate=Decimal(str(cfg["vat_rate"])),
                    irpf_rate=Decimal(str(cfg["irpf_rate"])),
                    vat_exempt=bool(cfg["vat_exempt"]),
                    withholding_applies=bool(cfg["withholding"]),
                )
            )

        return_date = None
        if cfg.get("deposit_returned") and lease.end_date is not None:
            return_date = lease.end_date + timedelta(days=30)
        session.add(
            Deposit(
                lease_id=lease.id,
                amount=Decimal(str(cfg["deposit"])),
                deposit_date=lease.start_date,
                agency=str(cfg["agency"]),
                return_date=return_date,
            )
        )
    session.flush()

    leases_by_property: dict[int, list[Lease]] = {}
    for cfg, lease in zip(_DEMO_LEASES, leases):
        property_id = units[int(cfg["unit"])].property_id
        leases_by_property.setdefault(property_id, []).append(lease)

    month = horizon_start
    while month <= current_month:
        for prop in properties:
            if rng.random() > 0.42:
                continue
            category, low, high = rng.choice(_DEMO_EXPENSE_TEMPLATES)
            candidates = leases_by_property.get(prop.id, [])
            linked_lease = rng.choice(candidates).id if candidates and rng.random() < 0.3 else None
            session.add(
                Expense(
                    property_id=prop.id,
                    lease_id=linked_lease,
                    category=category,
                    amount=Decimal(rng.randint(low, high)) / Decimal("100"),
                    expense_date=month.replace(day=rng.randint(1, 28)),
                    deductible=category != "supplies" or rng.random() < 0.4,
                    supplier=rng.choice(_DEMO_SUPPLIERS[category]),
                    invoice_number=(
                        f"F{rng.randint(1000, 9999)}-{month.year}" if rng.random() < 0.6 else None
                    ),
                )
            )
        month = _shift_months(month, 1)

    session.add(
        Expense(
            property_id=properties[0].id,
            category="repairs",
            amount=Decimal("125.00"),
            expense_date=_shift_months(current_month, -10).replace(day=15),
            deductible=True,
            supplier="Reformas Ibéricas",
            notes="Gasto duplicado (baja lógica de demostración)",
            deleted_at=datetime.now(UTC) - timedelta(days=30),
        )
    )
    session.flush()

    invoices: list[Invoice] = []
    payment_records: list[tuple[Payment, int, str, Tenant]] = []
    for month in _iter_months(horizon_start, current_month):
        period = _period(month)
        months_ago = (current_month.year - month.year) * 12 + (current_month.month - month.month)
        for lease_index, lease in enumerate(leases):
            cfg = _DEMO_LEASES[lease_index]
            if cfg["vat_rate"] is None or lease.start_date > month:
                continue
            if lease.end_date is not None and _month_start(lease.end_date) < month:
                continue

            rent = _rent_at(rent_schedules[lease_index], month)
            vat_rate = Decimal(str(cfg["vat_rate"]))
            irpf_rate = Decimal(str(cfg["irpf_rate"]))
            vat_amount = Decimal("0")
            irpf_withholding = Decimal("0")
            if not cfg["vat_exempt"]:
                vat_amount = (rent * vat_rate / Decimal("100")).quantize(Decimal("0.01"))
            if cfg["withholding"]:
                irpf_withholding = (rent * irpf_rate / Decimal("100")).quantize(Decimal("0.01"))
            total = rent + vat_amount - irpf_withholding

            invoice = Invoice(
                period=period,
                lease_id=lease.id,
                issue_date=month,
                due_date=month + timedelta(days=INVOICE_PAYMENT_TERMS_DAYS),
                status="issued",
                total_base=rent,
                total_vat=vat_amount,
                total_irpf_withholding=irpf_withholding,
                total=total,
            )
            _snapshot_parties(invoice, lease)
            InvoiceNumberingService.assign_number(session, invoice)
            session.add(
                InvoiceLine(
                    invoice_id=invoice.id,
                    concept=f"Alquiler {period} - {units[int(cfg['unit'])].name}",
                    base_amount=rent,
                    vat_rate=vat_rate,
                    vat_amount=vat_amount,
                    irpf_rate=irpf_rate,
                    irpf_withholding=irpf_withholding,
                )
            )
            invoices.append(invoice)

            plan = _payment_plan(rng, months_ago, (lease_index, months_ago))
            if plan == "unpaid":
                continue
            payment_date = min(month + timedelta(days=rng.randint(1, 8)), today)
            amount = (
                invoice.total
                if plan == "paid"
                else (invoice.total / Decimal("2")).quantize(Decimal("0.01"))
            )
            payment = PaymentService.register(
                session,
                invoice.id,
                amount,
                payment_date,
                method=_payment_method(rng, units[int(cfg["unit"])].unit_type),
                notes=None if plan == "paid" else "Pago parcial: pendiente el resto",
            )
            payment_records.append((payment, lease_index, period, tenants[int(cfg["tenant"])]))
    session.flush()

    rectify_lease_index, rectify_months_ago = _DEMO_RECTIFY
    rectify_period = _period(_shift_months(current_month, -rectify_months_ago))
    target_invoice = next(
        (
            invoice
            for invoice in invoices
            if invoice.lease_id == leases[rectify_lease_index].id
            and invoice.period == rectify_period
        ),
        None,
    )
    if target_invoice is not None:
        InvoiceService.rectify(
            session,
            target_invoice.id,
            "Error en la base imponible: se facturó la renta anterior a la revisión",
        )
        session.flush()

    cutoff = _shift_months(current_month, -6)
    for payment, lease_index, period, tenant in payment_records:
        if payment.method != "transferencia" or payment.payment_date < cutoff:
            continue
        roll = rng.random()
        if roll >= 0.8:
            continue
        entry_date = min(payment.payment_date + timedelta(days=rng.randint(0, 2)), today)
        movement = BankMovement(
            entry_date=entry_date,
            value_date=payment.payment_date,
            amount=payment.amount,
            concept=f"TRANSFERENCIA {tenant.name.upper()} ALQUILER {period}",
            iban_origin=_DEMO_IBANS[int(_DEMO_LEASES[lease_index]["tenant"]) % len(_DEMO_IBANS)],
            reference=f"REF{rng.randint(10000, 99999)}",
            status="unmatched",
        )
        session.add(movement)
        session.flush()
        if roll < 0.55:
            movement.status = "confirmed"
            session.add(movement)
            session.add(
                Reconciliation(
                    bank_movement_id=movement.id,
                    payment_id=payment.id,
                    score=Decimal("0.90"),
                    confirmed_at=datetime.combine(entry_date, time(9, 0), tzinfo=UTC),
                )
            )

    for days_ago, amount, concept in _DEMO_OTHER_MOVEMENTS:
        session.add(
            BankMovement(
                entry_date=today - timedelta(days=days_ago),
                value_date=today - timedelta(days=days_ago + 1),
                amount=Decimal(amount),
                concept=concept,
                status="unmatched",
            )
        )
    session.flush()

    return {
        "owners": _row_count(session, Owner),
        "properties": _row_count(session, Property),
        "units": _row_count(session, Unit),
        "tenants": _row_count(session, Tenant),
        "leases": _row_count(session, Lease),
        "rent_conditions": _row_count(session, RentCondition),
        "index_updates": _row_count(session, IndexUpdate),
        "tax_profiles": _row_count(session, TaxProfile),
        "deposits": _row_count(session, Deposit),
        "invoices": _row_count(session, Invoice),
        "invoice_lines": _row_count(session, InvoiceLine),
        "payments": _row_count(session, Payment),
        "expenses": _row_count(session, Expense),
        "bank_movements": _row_count(session, BankMovement),
        "reconciliations": _row_count(session, Reconciliation),
    }

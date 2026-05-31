from datetime import date, timedelta
from decimal import Decimal

from sqlmodel import Session, select

from app.jobs.daily_overdue import detect_overdue_invoices
from app.jobs.monthly_invoicing import generate_monthly_invoices
from app.models.event_log import EventLog
from app.models.invoice import Invoice
from app.models.lease import Lease, RentCondition, TaxProfile
from app.models.owner import Owner
from app.models.property import Property
from app.models.tenant import Tenant
from app.models.unit import Unit


def _create_lease(session: Session, monthly_rent: Decimal = Decimal("850.00")) -> Lease:
    owner = Owner(
        name="Owner", document_type="DNI", document_number="11111111A",
        email="o@t.com", phone="+34",
    )
    session.add(owner)
    session.flush()
    prop = Property(
        name="Prop", address="Addr", city="City", province="Prov",
        zip_code="28001", owner_id=owner.id,
    )
    session.add(prop)
    session.flush()
    unit = Unit(property_id=prop.id, name="Unit", unit_type="vivienda")
    session.add(unit)
    session.flush()
    tenant = Tenant(
        name="Tenant", document_type="DNI", document_number="22222222B",
        email="t@t.com", phone="+34",
    )
    session.add(tenant)
    session.flush()
    lease = Lease(
        unit_id=unit.id, tenant_id=tenant.id, owner_id=owner.id,
        start_date=date(2024, 1, 1), is_active=True,
    )
    session.add(lease)
    session.flush()
    rc = RentCondition(
        lease_id=lease.id, start_date=date(2024, 1, 1), monthly_rent=monthly_rent,
    )
    session.add(rc)
    tax = TaxProfile(
        lease_id=lease.id, vat_rate=Decimal("0"), irpf_rate=Decimal("0"),
        vat_exempt=True, withholding_applies=False,
    )
    session.add(tax)
    session.flush()
    return lease


class TestGenerateMonthlyInvoices:
    def test_produces_event_log_on_success(self, session: Session):
        _create_lease(session)

        invoices = generate_monthly_invoices("2024-06", session=session)

        assert len(invoices) >= 1

        logs = session.exec(
            select(EventLog).where(EventLog.event_type == "invoice_generation")
        ).all()
        assert len(logs) == 1
        assert "Generated" in logs[0].description

    def test_logs_error_on_failure(self, session: Session):
        owner = Owner(name="O", document_type="DNI", document_number="1",
                      email="o@t.com", phone="+34")
        session.add(owner)
        session.flush()
        prop = Property(name="P", address="A", city="C", province="P",
                        zip_code="28001", owner_id=owner.id)
        session.add(prop)
        session.flush()
        unit = Unit(property_id=prop.id, name="U", unit_type="vivienda")
        session.add(unit)
        session.flush()
        tenant = Tenant(name="T", document_type="DNI", document_number="2",
                        email="t@t.com", phone="+34")
        session.add(tenant)
        session.flush()
        lease = Lease(unit_id=unit.id, tenant_id=tenant.id, owner_id=owner.id,
                      start_date=date(2024, 1, 1), is_active=True)
        session.add(lease)
        session.flush()
        rc = RentCondition(lease_id=lease.id, start_date=date(2024, 1, 1),
                           monthly_rent=Decimal("500"))
        session.add(rc)
        session.flush()

        from app.services.invoice_service import InvoiceGenerationError

        try:
            generate_monthly_invoices("2024-06", session=session)
        except InvoiceGenerationError:
            pass

        logs = session.exec(
            select(EventLog).where(EventLog.event_type == "invoice_generation")
        ).all()
        assert any("Failed" in log.description for log in logs)


class TestDetectOverdue:
    def test_detects_old_unpaid_invoices(
        self, session: Session
    ):
        lease = _create_lease(session)
        old = date.today() - timedelta(days=45)
        inv = Invoice(
            period="2024-01",
            lease_id=lease.id,
            issue_date=old,
            status="draft",
            total_base=Decimal("850.00"),
            total_vat=Decimal("0"),
            total_irpf_withholding=Decimal("0"),
            total=Decimal("850.00"),
        )
        session.add(inv)
        session.flush()

        overdue = detect_overdue_invoices(session=session)

        assert len(overdue) >= 1
        assert overdue[0]["days_overdue"] >= 30

    def test_recent_invoice_not_overdue(self, session: Session):
        lease = _create_lease(session)
        inv = Invoice(
            period="2024-06",
            lease_id=lease.id,
            issue_date=date.today(),
            status="draft",
            total_base=Decimal("850.00"),
            total_vat=Decimal("0"),
            total_irpf_withholding=Decimal("0"),
            total=Decimal("850.00"),
        )
        session.add(inv)
        session.flush()

        overdue = detect_overdue_invoices(session=session)
        assert len(overdue) == 0

    def test_paid_invoice_not_overdue(self, session: Session):
        lease = _create_lease(session)
        old = date.today() - timedelta(days=45)
        inv = Invoice(
            period="2024-01",
            lease_id=lease.id,
            issue_date=old,
            status="paid",
            total_base=Decimal("850.00"),
            total_vat=Decimal("0"),
            total_irpf_withholding=Decimal("0"),
            total=Decimal("850.00"),
        )
        session.add(inv)
        session.flush()

        overdue = detect_overdue_invoices(session=session)
        assert len(overdue) == 0

    def test_logs_events_when_overdue_found(self, session: Session):
        lease = _create_lease(session)
        old = date.today() - timedelta(days=45)
        inv = Invoice(
            period="2024-01",
            lease_id=lease.id,
            issue_date=old,
            status="draft",
            total_base=Decimal("850.00"),
            total_vat=Decimal("0"),
            total_irpf_withholding=Decimal("0"),
            total=Decimal("850.00"),
        )
        session.add(inv)
        session.flush()

        detect_overdue_invoices(session=session)

        logs = session.exec(
            select(EventLog).where(EventLog.event_type == "overdue_detection")
        ).all()
        assert len(logs) == 1

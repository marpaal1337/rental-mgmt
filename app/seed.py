from datetime import date
from decimal import Decimal

from sqlmodel import Session, select

from app.database import engine
from app.models.lease import Deposit, Lease, RentCondition, TaxProfile
from app.models.owner import Owner
from app.models.property import Property
from app.models.tenant import Tenant
from app.models.unit import Unit


def seed():
    with Session(engine) as session:
        existing = session.exec(select(Owner)).first()
        if existing:
            print("Seed data already exists, skipping.")
            return

        owner = Owner(
            name="Juan Pérez García",
            document_type="DNI",
            document_number="12345678Z",
            email="juan@example.com",
            phone="+34 600 000 000",
            address="Calle Mayor 1, 28001 Madrid",
        )
        session.add(owner)
        session.flush()

        property = Property(
            name="Edificio Centro",
            address="Calle Gran Vía 10",
            city="Madrid",
            province="Madrid",
            zip_code="28013",
            cadastral_ref="1234567VK1234S0001WX",
            owner_id=owner.id,
        )
        session.add(property)
        session.flush()

        unit_vivienda = Unit(
            property_id=property.id,
            name="Piso 3º A",
            unit_type="vivienda",
            area_m2=85.0,
            is_active=True,
        )
        unit_local = Unit(
            property_id=property.id,
            name="Local Comercial Bajo",
            unit_type="local",
            area_m2=120.0,
            is_active=True,
        )
        session.add(unit_vivienda)
        session.add(unit_local)
        session.flush()

        tenant1 = Tenant(
            name="Ana Martínez López",
            document_type="DNI",
            document_number="87654321X",
            email="ana@email.com",
            phone="+34 611 111 111",
        )
        tenant2 = Tenant(
            name="Comercial Pérez SL",
            document_type="CIF",
            document_number="B12345678",
            email="info@comercialperez.es",
            phone="+34 622 222 222",
        )
        session.add(tenant1)
        session.add(tenant2)
        session.flush()

        lease1 = Lease(
            unit_id=unit_vivienda.id,
            tenant_id=tenant1.id,
            owner_id=owner.id,
            start_date=date(2024, 1, 1),
            is_active=True,
            notes="Contrato vivienda habitual",
        )
        lease2 = Lease(
            unit_id=unit_local.id,
            tenant_id=tenant2.id,
            owner_id=owner.id,
            start_date=date(2024, 2, 1),
            is_active=True,
            notes="Contrato local comercial",
        )
        session.add(lease1)
        session.add(lease2)
        session.flush()

        rent1 = RentCondition(
            lease_id=lease1.id,
            start_date=date(2024, 1, 1),
            monthly_rent=Decimal("850.00"),
        )
        rent2 = RentCondition(
            lease_id=lease2.id,
            start_date=date(2024, 2, 1),
            monthly_rent=Decimal("1500.00"),
        )
        session.add(rent1)
        session.add(rent2)

        tax1 = TaxProfile(
            lease_id=lease1.id,
            vat_rate=Decimal("0"),
            irpf_rate=Decimal("0"),
            vat_exempt=True,
            withholding_applies=False,
        )
        tax2 = TaxProfile(
            lease_id=lease2.id,
            vat_rate=Decimal("21.00"),
            irpf_rate=Decimal("19.00"),
            vat_exempt=False,
            withholding_applies=True,
        )
        session.add(tax1)
        session.add(tax2)

        deposit1 = Deposit(
            lease_id=lease1.id,
            amount=Decimal("850.00"),
            deposit_date=date(2024, 1, 1),
            agency="IVIMA",
        )
        deposit2 = Deposit(
            lease_id=lease2.id,
            amount=Decimal("3000.00"),
            deposit_date=date(2024, 2, 1),
            agency="IVIMA",
        )
        session.add(deposit1)
        session.add(deposit2)

        session.commit()

    print("Seed data created successfully.")


if __name__ == "__main__":
    seed()

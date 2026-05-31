import tempfile
from datetime import date
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

# Import all models to register them with SQLModel.metadata
import app.models.bank  # noqa
import app.models.expense  # noqa
import app.models.invoice  # noqa
import app.models.payment  # noqa
from app.database import get_session
from app.main import app as fastapi_app
from app.models.lease import Lease
from app.models.owner import Owner
from app.models.property import Property
from app.models.tenant import Tenant
from app.models.unit import Unit


@pytest.fixture
def session():
    engine = create_engine("sqlite://", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        db_url = f"sqlite:///{tmp.name}"
        eng = create_engine(db_url, echo=False)
        SQLModel.metadata.create_all(eng)

        def _override():
            sess = Session(eng)
            yield sess
            sess.close()

        fastapi_app.dependency_overrides[get_session] = _override
        with TestClient(fastapi_app) as tc:
            yield tc
        fastapi_app.dependency_overrides.clear()


@pytest.fixture
def sample_lease(session: Session) -> Lease:
    owner = Owner(
        name="Test Owner",
        document_type="DNI",
        document_number="11111111A",
        email="owner@test.com",
        phone="+34 600 000 000",
    )
    session.add(owner)
    session.flush()

    property = Property(
        name="Test Property",
        address="Calle Test 1",
        city="Madrid",
        province="Madrid",
        zip_code="28001",
        owner_id=owner.id,
    )
    session.add(property)
    session.flush()

    unit = Unit(
        property_id=property.id,
        name="Test Unit",
        unit_type="vivienda",
        is_active=True,
    )
    session.add(unit)
    session.flush()

    tenant = Tenant(
        name="Test Tenant",
        document_type="DNI",
        document_number="22222222B",
        email="tenant@test.com",
        phone="+34 611 111 111",
    )
    session.add(tenant)
    session.flush()

    lease = Lease(
        unit_id=unit.id,
        tenant_id=tenant.id,
        owner_id=owner.id,
        start_date=date(2024, 1, 1),
        is_active=True,
    )
    session.add(lease)
    session.flush()

    return lease

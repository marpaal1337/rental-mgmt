from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.api.deps import verify_api_key
from app.api.schemas import TenantCreate, TenantUpdate
from app.database import get_session
from app.models.tenant import Tenant

router = APIRouter(
    prefix="/tenants",
    tags=["tenants"],
    dependencies=[Depends(verify_api_key)],
)


@router.get("")
def list_tenants(session: Session = Depends(get_session)):
    return session.exec(select(Tenant).where(Tenant.deleted_at.is_(None))).all()


@router.get("/{tenant_id}")
def get_tenant(tenant_id: int, session: Session = Depends(get_session)):
    tenant = session.get(Tenant, tenant_id)
    if tenant is None or tenant.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.post("", status_code=201)
def create_tenant(body: TenantCreate, session: Session = Depends(get_session)):
    tenant = Tenant(**body.model_dump())
    session.add(tenant)
    session.commit()
    session.refresh(tenant)
    return tenant


@router.put("/{tenant_id}")
def update_tenant(tenant_id: int, body: TenantUpdate, session: Session = Depends(get_session)):
    tenant = session.get(Tenant, tenant_id)
    if tenant is None or tenant.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(tenant, field, value)
    tenant.updated_at = datetime.now(UTC)
    session.add(tenant)
    session.commit()
    session.refresh(tenant)
    return tenant


@router.delete("/{tenant_id}")
def delete_tenant(tenant_id: int, session: Session = Depends(get_session)):
    tenant = session.get(Tenant, tenant_id)
    if tenant is None or tenant.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    tenant.deleted_at = datetime.now(UTC)
    session.commit()
    return {"detail": "Tenant deleted"}

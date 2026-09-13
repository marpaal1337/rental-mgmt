from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.api.deps import verify_api_key
from app.database import get_session
from app.services.fiscal_service import FiscalError, FiscalService

router = APIRouter(
    prefix="/fiscal",
    tags=["fiscal"],
    dependencies=[Depends(verify_api_key)],
)


@router.get("/vat")
def vat_report(
    year: int = Query(..., ge=2000, le=2100),
    quarter: int = Query(..., ge=1, le=4),
    session: Session = Depends(get_session),
):
    """IVA trimestral (modelo 303)."""
    try:
        return FiscalService.vat_report(session, year, quarter)
    except FiscalError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/withholdings")
def withholdings_report(
    year: int = Query(..., ge=2000, le=2100),
    session: Session = Depends(get_session),
):
    """Retenciones de IRPF soportadas (modelo 190)."""
    try:
        return FiscalService.withholdings_report(session, year)
    except FiscalError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/income")
def income_report(
    year: int = Query(..., ge=2000, le=2100),
    session: Session = Depends(get_session),
):
    """Rendimiento del capital inmobiliario por propiedad (modelo 100)."""
    try:
        return FiscalService.income_report(session, year)
    except FiscalError as e:
        raise HTTPException(status_code=400, detail=str(e))

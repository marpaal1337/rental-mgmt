from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.api.deps import verify_api_key
from app.api.schemas import InvoiceGenerateRequest
from app.database import get_session
from app.models.invoice import Invoice
from app.services.invoice_service import InvoiceGenerationError, InvoiceService
from app.services.pdf_service import PDFGenerationError, PDFService

router = APIRouter(
    prefix="/invoices",
    tags=["invoices"],
    dependencies=[Depends(verify_api_key)],
)


@router.get("")
def list_invoices(session: Session = Depends(get_session)):
    return session.exec(select(Invoice).where(Invoice.deleted_at.is_(None))).all()


@router.get("/{invoice_id}")
def get_invoice(invoice_id: int, session: Session = Depends(get_session)):
    invoice = session.get(Invoice, invoice_id)
    if invoice is None or invoice.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.post("/generate", status_code=201)
def generate_invoices(
    body: InvoiceGenerateRequest,
    session: Session = Depends(get_session),
):
    try:
        invoices = InvoiceService.generate_monthly(session, body.period)
        session.commit()
        return invoices
    except InvoiceGenerationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{invoice_id}/pdf")
def download_invoice_pdf(
    invoice_id: int,
    session: Session = Depends(get_session),
):
    try:
        path = PDFService.render_invoice(session, invoice_id)
        from fastapi.responses import FileResponse

        return FileResponse(
            path,
            media_type="application/pdf",
            filename=f"factura-{invoice_id}.pdf",
        )
    except PDFGenerationError as e:
        raise HTTPException(status_code=404, detail=str(e))

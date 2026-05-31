from decimal import Decimal
from pathlib import Path
from typing import List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlmodel import Session

from app.models.invoice import Invoice


class PDFGenerationError(Exception):
    """Raised when PDF generation fails."""


INVOICES_DIR = Path("data") / "invoices"


class PDFService:
    @staticmethod
    def render_invoice(
        session: Session, invoice_id: int
    ) -> Path:
        invoice = session.get(Invoice, invoice_id)
        if invoice is None:
            raise PDFGenerationError(f"Invoice {invoice_id} not found")

        lines = invoice.lines
        if not lines:
            raise PDFGenerationError(
                f"Invoice {invoice_id} has no lines"
            )

        lease = invoice.lease
        owner = lease.owner
        tenant = lease.tenant

        year, month = invoice.period.split("-")
        out_dir = INVOICES_DIR / year / month
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{invoice.id}.pdf"

        doc = SimpleDocTemplate(
            str(out_path),
            pagesize=A4,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
            leftMargin=25 * mm,
            rightMargin=20 * mm,
        )
        styles = getSampleStyleSheet()
        elements: list = []

        normal = styles["Normal"]
        heading = styles["Heading1"]

        heading.alignment = 1
        elements.append(Paragraph("FACTURA", heading))
        elements.append(
            Paragraph(
                f"Nº INV-{year}-{invoice.id:04d}",
                styles["Normal"],
            )
        )
        elements.append(Spacer(1, 10 * mm))

        inv_num = f"INV-{year}-{invoice.id:04d}"
        period_display = f"{month}/{year}"

        data_metadata: List[List[str]] = [
            ["Nº Factura:", inv_num, "Fecha:", str(invoice.issue_date)],
            ["Periodo:", period_display, "Estado:", invoice.status],
        ]
        meta_table = Table(data_metadata, colWidths=[35 * mm, 50 * mm, 30 * mm, 50 * mm])
        meta_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                ]
            )
        )
        elements.append(meta_table)
        elements.append(Spacer(1, 8 * mm))

        owner_lines = [
            f"<b>Arrendador:</b> {owner.name}",
            f"{owner.document_type}: {owner.document_number}",
            owner.email,
            owner.phone,
        ]
        if owner.address:
            owner_lines.append(owner.address)
        elements.append(Paragraph("<br/>".join(owner_lines), normal))
        elements.append(Spacer(1, 5 * mm))

        tenant_lines = [
            f"<b>Arrendatario:</b> {tenant.name}",
            f"{tenant.document_type}: {tenant.document_number}",
            tenant.email,
            tenant.phone,
        ]
        elements.append(Paragraph("<br/>".join(tenant_lines), normal))
        elements.append(Spacer(1, 8 * mm))

        header = ["Concepto", "Base", "IVA%", "Cuota IVA", "IRPF%", "Retención"]
        body = [
            [
                Paragraph(line.concept, normal),
                PDFService._fmt(line.base_amount),
                f"{line.vat_rate:.2f}%",
                PDFService._fmt(line.vat_amount),
                f"{line.irpf_rate:.2f}%",
                PDFService._fmt(line.irpf_withholding),
            ]
            for line in lines
        ]
        table_data = [header] + body
        col_widths = [55 * mm, 25 * mm, 18 * mm, 25 * mm, 18 * mm, 25 * mm]
        line_table = Table(table_data, colWidths=col_widths)
        line_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2F5496")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#F2F2F2")],
                    ),
                ]
            )
        )
        elements.append(line_table)
        elements.append(Spacer(1, 6 * mm))

        total_data: List[List[str]] = [
            ["Base Imponible:", PDFService._fmt(invoice.total_base)],
            ["Cuota IVA:", PDFService._fmt(invoice.total_vat)],
            ["Retención IRPF:", PDFService._fmt(invoice.total_irpf_withholding)],
        ]
        total_table = Table(total_data, colWidths=[140 * mm, 30 * mm])
        total_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("LINEABOVE", (0, -2), (-1, -2), 0.5, colors.grey),
                ]
            )
        )
        elements.append(total_table)
        elements.append(Spacer(1, 2 * mm))

        total_final = [
            [
                Paragraph(
                    f"<b>TOTAL:</b> {PDFService._fmt(invoice.total)} €",
                    styles["Heading2"],
                )
            ]
        ]
        final_table = Table(total_final, colWidths=[170 * mm])
        final_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                    ("LINEABOVE", (0, 0), (-1, 0), 2, colors.HexColor("#2F5496")),
                    ("LINEBELOW", (0, 0), (-1, 0), 2, colors.HexColor("#2F5496")),
                ]
            )
        )
        elements.append(final_table)
        elements.append(Spacer(1, 10 * mm))

        elements.append(
            Paragraph(
                "Documento generado electrónicamente. "
                "Pie de factura — IVA e IRPF según legislación vigente.",
                styles["Normal"],
            )
        )

        doc.build(elements)
        return out_path

    @staticmethod
    def _fmt(value: Decimal) -> str:
        return f"{value:.2f} €"

import logging
from datetime import UTC, datetime
from decimal import Decimal

from sqlmodel import Session, select

from app.models.bank import BankMovement, Reconciliation
from app.models.invoice import Invoice
from app.models.lease import Lease
from app.models.payment import Payment
from app.models.tenant import Tenant
from app.services.bank_adapter import BaseBankAdapter

logger = logging.getLogger(__name__)


class ReconciliationError(Exception):
    pass


class ReconciliationService:
    MATCH_WINDOW_DAYS = 5
    MIN_SCORE = Decimal("0.3")

    @staticmethod
    def import_csv(
        session: Session,
        file_path: str,
        adapter: BaseBankAdapter,
    ) -> list[BankMovement]:
        rows = adapter.parse(file_path)

        existing = {
            (m.entry_date, m.amount, m.concept, m.iban_origin)
            for m in session.exec(select(BankMovement)).all()
        }

        movements: list[BankMovement] = []
        seen = set(existing)
        duplicates = 0
        for row in rows:
            fingerprint = (
                row.entry_date,
                row.amount,
                row.concept[:500],
                row.iban_origin,
            )
            if fingerprint in seen:
                duplicates += 1
                continue
            seen.add(fingerprint)
            movement = BankMovement(
                entry_date=row.entry_date,
                value_date=row.value_date,
                amount=row.amount,
                concept=row.concept[:500],
                iban_origin=row.iban_origin,
                reference=row.reference,
                status="unmatched",
                raw_data=row.raw,
            )
            session.add(movement)
            movements.append(movement)

        if duplicates:
            logger.info("Skipped %d duplicate bank movements on import", duplicates)

        return movements

    @staticmethod
    def propose_matches(
        session: Session,
        bank_movement_id: int,
    ) -> list[Reconciliation]:
        movement = session.get(BankMovement, bank_movement_id)
        if movement is None or movement.deleted_at is not None:
            raise ReconciliationError(f"BankMovement {bank_movement_id} not found")

        if movement.status != "unmatched":
            raise ReconciliationError(f"BankMovement {bank_movement_id} already {movement.status}")

        matched_payment_ids = set(
            session.exec(
                select(Reconciliation.payment_id).where(
                    Reconciliation.confirmed_at.is_not(None),
                    Reconciliation.deleted_at.is_(None),
                )
            ).all()
        )

        recurring_payment_ids: set[int] = set()
        if movement.iban_origin:
            recurring_payment_ids = set(
                session.exec(
                    select(Reconciliation.payment_id)
                    .join(
                        BankMovement,
                        Reconciliation.bank_movement_id == BankMovement.id,
                    )
                    .where(
                        BankMovement.iban_origin == movement.iban_origin,
                        Reconciliation.confirmed_at.is_not(None),
                        Reconciliation.deleted_at.is_(None),
                    )
                ).all()
            )

        candidates: list[tuple[Payment, Decimal]] = []
        payment_rows = session.exec(
            select(Payment, Invoice, Tenant)
            .join(Invoice, Payment.invoice_id == Invoice.id)
            .join(Lease, Invoice.lease_id == Lease.id)
            .join(Tenant, Lease.tenant_id == Tenant.id)
            .where(
                Payment.deleted_at.is_(None),
                Invoice.deleted_at.is_(None),
            )
        ).all()

        for payment, invoice, tenant in payment_rows:
            if payment.id in matched_payment_ids:
                continue
            score = ReconciliationService._match_score(
                movement, payment, invoice, tenant, recurring_payment_ids
            )
            if score >= ReconciliationService.MIN_SCORE:
                candidates.append((payment, score))

        candidates.sort(key=lambda x: x[1], reverse=True)

        previous = session.exec(
            select(Reconciliation).where(
                Reconciliation.bank_movement_id == movement.id,
                Reconciliation.confirmed_at.is_(None),
            )
        ).all()
        for stale in previous:
            session.delete(stale)

        reconciliations: list[Reconciliation] = []
        for payment, score in candidates:
            reconciliations.append(
                Reconciliation(
                    bank_movement_id=movement.id,
                    payment_id=payment.id,
                    score=score,
                )
            )

        for r in reconciliations:
            session.add(r)

        if reconciliations:
            movement.status = "proposed"
            session.add(movement)

        return reconciliations

    @staticmethod
    def _match_score(
        movement: BankMovement,
        payment: Payment,
        invoice: Invoice,
        tenant: Tenant,
        recurring_payment_ids: set[int],
    ) -> Decimal:
        score = Decimal("0")
        if movement.amount == payment.amount:
            score += Decimal("0.5")

        days_diff = abs((movement.entry_date - payment.payment_date).days)
        if days_diff <= ReconciliationService.MATCH_WINDOW_DAYS:
            score += Decimal("0.3") * (
                Decimal("1")
                - Decimal(str(days_diff)) / Decimal(str(ReconciliationService.MATCH_WINDOW_DAYS))
            )

        concept_words = {
            word.strip(".,;:()/-").lower()
            for word in movement.concept.split()
            if len(word.strip(".,;:()/-")) > 2
        }
        reference_words = {
            word.lower() for word in (tenant.name or "").split() if len(word) > 2
        }
        reference_words.update(invoice.period.split("-"))
        if concept_words & reference_words:
            score += Decimal("0.1")

        if payment.id in recurring_payment_ids:
            score += Decimal("0.1")

        return min(score, Decimal("1"))

    @staticmethod
    def confirm_match(
        session: Session,
        reconciliation_id: int,
    ) -> Reconciliation:
        reconciliation = session.get(Reconciliation, reconciliation_id)
        if reconciliation is None or reconciliation.deleted_at is not None:
            raise ReconciliationError(f"Reconciliation {reconciliation_id} not found")

        movement = reconciliation.bank_movement
        if movement.status == "confirmed":
            raise ReconciliationError(f"BankMovement {movement.id} already confirmed")

        reconciliation.confirmed_at = datetime.now(UTC)
        movement.status = "confirmed"
        session.add(reconciliation)
        session.add(movement)

        siblings = session.exec(
            select(Reconciliation).where(
                Reconciliation.bank_movement_id == movement.id,
                Reconciliation.id != reconciliation.id,
                Reconciliation.confirmed_at.is_(None),
            )
        ).all()
        for sibling in siblings:
            session.delete(sibling)

        return reconciliation

    @staticmethod
    def list_unmatched(
        session: Session,
    ) -> list[BankMovement]:
        return list(
            session.exec(
                select(BankMovement).where(
                    BankMovement.status == "unmatched",
                    BankMovement.deleted_at.is_(None),
                )
            ).all()
        )

    @staticmethod
    def list_proposed(
        session: Session,
    ) -> list[BankMovement]:
        return list(
            session.exec(
                select(BankMovement).where(
                    BankMovement.status == "proposed",
                    BankMovement.deleted_at.is_(None),
                )
            ).all()
        )

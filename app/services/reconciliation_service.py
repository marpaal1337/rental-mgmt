from datetime import UTC, datetime
from decimal import Decimal

from sqlmodel import Session, select

from app.models.bank import BankMovement, Reconciliation
from app.models.payment import Payment
from app.services.bank_adapter import BaseBankAdapter


class ReconciliationError(Exception):
    pass


class ReconciliationService:
    MATCH_WINDOW_DAYS = 5

    @staticmethod
    def import_csv(
        session: Session,
        file_path: str,
        adapter: BaseBankAdapter,
    ) -> list[BankMovement]:
        rows = adapter.parse(file_path)
        movements: list[BankMovement] = []
        for row in rows:
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

        candidates: list[tuple[Payment, Decimal]] = []
        payments = session.exec(select(Payment).where(Payment.deleted_at.is_(None))).all()

        for payment in payments:
            score = ReconciliationService._match_score(movement, payment)
            if score > 0:
                candidates.append((payment, score))

        candidates.sort(key=lambda x: x[1], reverse=True)

        reconciliations: list[Reconciliation] = []
        for payment, score in candidates:
            existing = session.exec(
                select(Reconciliation).where(
                    Reconciliation.payment_id == payment.id,
                    Reconciliation.confirmed_at.is_not(None),
                    Reconciliation.deleted_at.is_(None),
                )
            ).first()
            if existing is not None:
                continue

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
    def _match_score(movement: BankMovement, payment: Payment) -> Decimal:
        score = Decimal("0")
        if movement.amount == payment.amount:
            score += Decimal("0.5")

        days_diff = abs((movement.entry_date - payment.payment_date).days)
        if days_diff <= ReconciliationService.MATCH_WINDOW_DAYS:
            score += Decimal("0.3") * (
                Decimal("1")
                - Decimal(str(days_diff)) / Decimal(str(ReconciliationService.MATCH_WINDOW_DAYS))
            )

        common_words = set(movement.concept.lower().split()) & set(
            str(payment.invoice_id).lower().split()
        )
        if common_words:
            score += Decimal("0.1")

        if movement.iban_origin:
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

        reconciliation.confirmed_at = datetime.now(UTC)
        reconciliation.bank_movement.status = "confirmed"
        session.add(reconciliation)
        session.add(reconciliation.bank_movement)
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

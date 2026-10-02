from decimal import Decimal

from app.database.repositories.cash_movement_repository import (
    CashMovementRepository
)

from app.database.repositories.settlement_repository import (
    SettlementRepository
)

from app.financial.models import (
    ReconciliationDirection,
    ReconciliationStatus
)

from app.financial.reconciliation_service import (
    ReconciliationService
)


def test_reconcile_settlement_with_actual_cash_movement(
    db_connection,
    test_settlement,
    test_account
):

    with db_connection.cursor() as cursor:

        cursor.execute(
            """
            INSERT INTO financial.cash_movements (
                settlement_id,
                account_id,
                movement_type,
                direction,
                amount,
                currency,
                status,
                movement_date
            )
            VALUES (
                %s,
                %s,
                'TAX',
                'CREDIT',
                11000.00,
                'INR',
                'COMPLETED',
                CURRENT_TIMESTAMP
            )
            """,
            (
                test_settlement,
                test_account
            )
        )

    settlement_repository = SettlementRepository(
        db_connection
    )

    cash_movement_repository = CashMovementRepository(
        db_connection
    )

    service = ReconciliationService(
        settlement_repository,
        cash_movement_repository
    )

    result = service.reconcile_settlement(
        test_settlement
    )

    assert result.status == ReconciliationStatus.MATCH.value

    assert result.reconciliation_direction == ReconciliationDirection.MATCH.value

    assert result.expected_cash == Decimal("11000.00")

    assert result.actual_cash == Decimal("11000.00")

    assert result.difference == Decimal("0.00")

    assert result.absolute_difference == Decimal("0.00")

def test_reconcile_settlement_with_missing_cash(
    db_connection,
    test_settlement
):

    settlement_repository = SettlementRepository(
        db_connection
    )

    cash_movement_repository = CashMovementRepository(
        db_connection
    )

    service = ReconciliationService(
        settlement_repository,
        cash_movement_repository
    )

    result = service.reconcile_settlement(
        test_settlement
    )

    assert result.status == ReconciliationStatus.MISMATCH.value

    assert (
        result.reconciliation_direction
        == ReconciliationDirection.SHORTFALL.value
    )

    assert result.expected_cash == Decimal("11000.00")

    assert result.actual_cash == Decimal("0.00")

    assert result.difference == Decimal("-11000.00")

    assert result.absolute_difference == Decimal("11000.00")
from decimal import Decimal
from app.financial.models import CashMovementStatus, CashMovementDirection
from app.database.repositories.cash_movement_repository import (
    CashMovementRepository
)


def test_get_cash_movements_by_settlement(
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
            RETURNING cash_movement_id;
            """,
            (
                test_settlement,
                test_account
            )
        )

        cash_movement_id = cursor.fetchone()[0]

    repository = CashMovementRepository(
        db_connection
    )

    results = repository.get_by_settlement(
        test_settlement
    )

    assert len(results) == 1

    result = results[0]

    assert result.cash_movement_id == cash_movement_id
    assert result.settlement_id == test_settlement
    assert result.account_id == test_account
    assert result.amount == Decimal("11000.00")
    assert result.currency.strip() == "INR"
    assert result.direction == CashMovementDirection.CREDIT
    assert result.status == CashMovementStatus.COMPLETED
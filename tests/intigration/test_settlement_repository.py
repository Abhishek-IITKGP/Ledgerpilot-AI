from decimal import Decimal

from app.database.repositories.settlement_repository import (
    SettlementRepository
)


def test_get_cash_data(db_connection, test_transaction):

    with db_connection.cursor() as cursor:

        cursor.execute(
            """
            INSERT INTO financial.settlements (
                transaction_id,
                settlement_type,
                expected_cash_amount,
                settled_cash_amount,
                status,
                failure_reason
            )
            VALUES (
                %s,
                'CASH_RECEIVABLE',
                15000.00,
                14500.00,
                'FAILED',
                'TEST_FAILURE'
            )
            RETURNING settlement_id;
            """,
            (test_transaction,)
        )

        settlement_id = cursor.fetchone()[0]

    repository = SettlementRepository(db_connection)

    result = repository.get_cash_data(
        settlement_id
    )

    assert result.settlement_id == settlement_id
    assert result.expected_cash == Decimal("15000.00")
    assert result.actual_cash == Decimal("14500.00")
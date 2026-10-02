from decimal import Decimal

from app.application import create_investigation_workflow


def test_gs001_investigation_workflow(db_connection):

    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT s.settlement_id
            FROM financial.customers c
            JOIN financial.accounts a
                ON a.customer_id = c.customer_id
            JOIN financial.orders o
                ON o.account_id = a.account_id
            JOIN financial.securities sec
                ON sec.security_id = o.security_id
            JOIN financial.transactions t
                ON t.order_id = o.order_id
            JOIN financial.settlements s
                ON s.transaction_id = t.transaction_id
            WHERE c.email = %s
              AND sec.ticker = %s
              AND o.side = 'SELL'
              AND o.quantity = 20
              AND o.status = 'COMPLETED'
              AND t.transaction_type = 'SELL'
              AND t.gross_amount = 11000.00
              AND t.status = 'COMPLETED'
              AND s.settlement_type = 'CASH_RECEIVABLE'
              AND s.expected_cash_amount = 11000.00
              AND s.status = 'FAILED'
              AND s.failure_reason = 'INVALID_SETTLEMENT_INSTRUCTION'
            ORDER BY s.settlement_id DESC
            LIMIT 1
            """,
            (
                "rahul.sharma@finsight.example",
                "ABC",
            ),
        )

        row = cursor.fetchone()

    assert row is not None, (
        "GS-001 was not found. Run scripts/seed_gs001.sql first."
    )

    settlement_id = row[0]

    workflow = create_investigation_workflow(db_connection)

    finding = workflow.investigate_settlement(settlement_id)

    assert finding is not None

    assert finding.root_causes == [
        "INVALID_SETTLEMENT_INSTRUCTION",
        "CASH_MOVEMENT_MISMATCH",
    ]

    assert finding.impact == Decimal("11000.00")
    assert finding.severity == "HIGH"

    assert (
        "No completed cash movement was recorded"
        in finding.evidence
    )

    assert (
        "Review the settlement instruction and investigate the "
        "cash movement discrepancy before reprocessing settlement."
        == finding.recommended_action
    )
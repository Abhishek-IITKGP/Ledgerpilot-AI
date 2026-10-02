from datetime import datetime, timezone
from decimal import Decimal

from app.investigation.models import ExecutionEvidence, InvestigationCase, InvestigationContext, OrderEvidence, SettlementEvidence, TransactionEvidence


def test_settlement_evidence():

    evidence = SettlementEvidence(
        settlement_id=1,
        transaction_id=1,
        settlement_type="CASH_RECEIVABLE",
        expected_cash=Decimal("11000.00"),
        settled_cash=Decimal("0.00"),
        status="FAILED",
        failure_reason="INVALID_SETTLEMENT_INSTRUCTION"
    )

    assert evidence.settlement_id == 1

    assert evidence.transaction_id == 1

    assert evidence.expected_cash == Decimal("11000.00")

    assert evidence.settled_cash == Decimal("0.00")

    assert evidence.status == "FAILED"

    assert (
        evidence.failure_reason
        == "INVALID_SETTLEMENT_INSTRUCTION"
    )

def test_transaction_evidence():

    evidence = TransactionEvidence(
        transaction_id=1,
        transaction_type="SELL",
        gross_amount=Decimal("11000.00"),
        fee_amount=Decimal("0.00"),
        net_amount=Decimal("11000.00"),
        status="COMPLETED",
        order_id=1
    )

    assert evidence.transaction_id == 1

    assert evidence.transaction_type == "SELL"

    assert evidence.gross_amount == Decimal("11000.00")

    assert evidence.fee_amount == Decimal("0.00")

    assert evidence.net_amount == Decimal("11000.00")

    assert evidence.status == "COMPLETED"



def test_execution_evidence():

    execution_time = datetime(
        2026,
        8,
        31,
        10,
        30,
        tzinfo=timezone.utc
    )

    evidence = ExecutionEvidence(
        execution_id=1,
        order_id=1,
        execution_quantity=20,
        execution_price=Decimal("550.00"),
        execution_time=execution_time,
        status="COMPLETED"
    )

    assert evidence.execution_id == 1

    assert evidence.order_id == 1

    assert evidence.execution_quantity == 20

    assert evidence.execution_price == Decimal("550.00")

    assert evidence.execution_time == execution_time

    assert evidence.status == "COMPLETED"



def test_investigation_context_contains_all_evidence():
    case = InvestigationCase(
        investigation_id=None,
        settlement_id=1,
        expected_cash=Decimal("11000.00"),
        actual_cash=Decimal("0.00"),
        discrepancy=Decimal("11000.00"),
    )

    settlement = SettlementEvidence(
        settlement_id=1,
        transaction_id=1,
        settlement_type="CASH",
        expected_cash=Decimal("11000.00"),
        settled_cash=Decimal("0.00"),
        status="FAILED",
        failure_reason="INVALID_SETTLEMENT_INSTRUCTION",
    )

    transaction = TransactionEvidence(
        transaction_id=1,
        transaction_type="SELL",
        gross_amount=Decimal("11000.00"),
        fee_amount=Decimal("0.00"),
        net_amount=Decimal("11000.00"),
        status="COMPLETED",
        order_id=1
    )

    order = OrderEvidence(
        order_id=1,
        account_id=1,
        security_id=1,
        side="SELL",
        order_type="MARKET",
        quantity=20,
        limit_price=None,
        status="COMPLETED",
        created_at=None,
    )

    executions = []

    cash_movements = []

    context = InvestigationContext(
        case=case,
        settlement=settlement,
        transaction=transaction,
        order=order,
        executions=executions,
        cash_movements=cash_movements,
    )

    assert context.case == case
    assert context.settlement == settlement
    assert context.transaction == transaction
    assert context.order == order
    assert context.executions == executions
    assert context.cash_movements == cash_movements
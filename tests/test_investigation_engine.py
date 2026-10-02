from datetime import datetime, timezone
from decimal import Decimal

from app.financial.models import CashMovementData, CashMovementDirection
from app.investigation.investigation_engine import InvestigationEngine
from app.investigation.models import (
    ExecutionEvidence,
    InvestigationCase,
    InvestigationContext,
    OrderEvidence,
    SettlementEvidence,
    TransactionEvidence,
)


def test_investigation_uses_completed_financial_facts_only():
    context = InvestigationContext(
        case=InvestigationCase(
            investigation_id=None,
            settlement_id=1,
            expected_cash=Decimal("11000.00"),
            actual_cash=Decimal("0.00"),
            discrepancy=Decimal("11000.00"),
        ),
        settlement=SettlementEvidence(
            settlement_id=1,
            transaction_id=1,
            settlement_type="CASH_RECEIVABLE",
            expected_cash=Decimal("11000.00"),
            settled_cash=Decimal("0.00"),
            status="FAILED",
            failure_reason="INVALID_SETTLEMENT_INSTRUCTION",
        ),
        transaction=TransactionEvidence(
            transaction_id=1,
            transaction_type="SELL",
            gross_amount=Decimal("11000.00"),
            fee_amount=Decimal("0.00"),
            net_amount=Decimal("11000.00"),
            status="COMPLETED",
            order_id=1,
        ),
        order=OrderEvidence(
            order_id=1,
            account_id=1,
            security_id=1,
            side="SELL",
            order_type="MARKET",
            quantity=20,
            limit_price=None,
            status="COMPLETED",
            created_at=datetime.now(timezone.utc),
        ),
        executions=[
            ExecutionEvidence(
                execution_id=1,
                order_id=1,
                execution_quantity=20,
                execution_price=Decimal("550.00"),
                execution_time=datetime.now(timezone.utc),
                status="COMPLETED",
            ),
            ExecutionEvidence(
                execution_id=2,
                order_id=1,
                execution_quantity=20,
                execution_price=Decimal("550.00"),
                execution_time=datetime.now(timezone.utc),
                status="FAILED",
            ),
        ],
        cash_movements=[
            CashMovementData(
                cash_movement_id=1,
                settlement_id=1,
                account_id=1,
                movement_type="TRADE_PROCEEDS",
                direction=CashMovementDirection.CREDIT,
                amount=Decimal("11000.00"),
                currency="USD",
                status="PENDING",
            )
        ],
    )

    finding = InvestigationEngine().investigate(context)

    assert "CASH_MOVEMENT_MISMATCH" in finding.root_causes
    assert "EXECUTION_TRANSACTION_MISMATCH" not in finding.root_causes
    assert "ORDER_EXECUTION_MISMATCH" not in finding.root_causes
    assert "No completed cash movement was recorded" in finding.evidence
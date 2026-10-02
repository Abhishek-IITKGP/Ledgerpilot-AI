from decimal import Decimal
from unittest.mock import Mock

from app.financial.models import (
    ReconciliationDirection,
    ReconciliationResult,
    ReconciliationStatus
)

from app.investigation.investigation_service import (
    InvestigationService
)
from app.investigation.models import ExecutionEvidence, InvestigationContext, OrderEvidence, SettlementEvidence, TransactionEvidence


def test_create_investigation_case_for_mismatch():

    settlement_repository = Mock()
    transaction_repository = Mock()
    order_repository = Mock()
    execution_repository = Mock()
    cash_movement_repository = Mock()

    reconciliation_result = ReconciliationResult(
        expected_cash=Decimal("11000.00"),
        actual_cash=Decimal("0.00"),
        difference=Decimal("-11000.00"),
        absolute_difference=Decimal("11000.00"),
        status=ReconciliationStatus.MISMATCH,
        reconciliation_direction=ReconciliationDirection.SHORTFALL
    )

    service = InvestigationService(
            settlement_repository,
            transaction_repository,
            order_repository,
            execution_repository,
            cash_movement_repository
        )

    case = service.create_case(
        settlement_id=1,
        reconciliation_result=reconciliation_result
    )

    assert case.settlement_id == 1

    assert case.expected_cash == Decimal("11000.00")

    assert case.actual_cash == Decimal("0.00")

    assert case.discrepancy == Decimal("11000.00")

def test_no_investigation_case_for_match():
    settlement_repository = Mock()
    transaction_repository = Mock()
    order_repository = Mock()
    execution_repository = Mock()
    cash_movement_repository = Mock()

    
    reconciliation_result = ReconciliationResult(
        expected_cash=Decimal("11000.00"),
                actual_cash=Decimal("11000.00"),
                difference=Decimal("0.00"),
                absolute_difference=Decimal("0.00"),
                status=ReconciliationStatus.MATCH,
                reconciliation_direction=ReconciliationDirection.MATCH
    )

    service = InvestigationService(
        settlement_repository,
        transaction_repository,
        order_repository,
        execution_repository,
        cash_movement_repository
    )
    case = service.create_case(
        settlement_id = 1,
        reconciliation_result = reconciliation_result
    )

    assert case is None


def test_build_investigation_context():
    settlement_repository = Mock()
    transaction_repository = Mock()
    order_repository = Mock()
    execution_repository = Mock()
    cash_movement_repository = Mock()

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

    executions = [
        ExecutionEvidence(
            execution_id=1,
            order_id=1,
            execution_quantity=20,
            execution_price=Decimal("550.00"),
            execution_time=None,
            status="COMPLETED",
        )
    ]

    cash_movements = []

    settlement_repository.get_investigation_data.return_value = settlement
    transaction_repository.get_investigation_data.return_value = transaction
    order_repository.get_investigation_data.return_value = order
    execution_repository.get_investigation_data.return_value = executions
    cash_movement_repository.get_by_settlement.return_value = cash_movements

    reconciliation_result = Mock()
    reconciliation_result.expected_cash = Decimal("11000.00")
    reconciliation_result.actual_cash = Decimal("0.00")
    reconciliation_result.absolute_difference = Decimal("11000.00")

    service = InvestigationService(
        settlement_repository,
        transaction_repository,
        order_repository,
        execution_repository,
        cash_movement_repository,
    )

    context = service.build_investigation_context(
        settlement_id=1,
        reconciliation_result=reconciliation_result,
    )

    assert isinstance(context, InvestigationContext)

    assert context.case.settlement_id == 1
    assert context.case.expected_cash == Decimal("11000.00")
    assert context.case.actual_cash == Decimal("0.00")
    assert context.case.discrepancy == Decimal("11000.00")

    assert context.settlement == settlement
    assert context.transaction == transaction
    assert context.order == order
    assert context.executions == executions
    assert context.cash_movements == cash_movements
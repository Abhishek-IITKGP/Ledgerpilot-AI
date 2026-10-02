from decimal import Decimal
from app.financial.models import CashMovementDirection, CashMovementStatus
from app.financial.cash_reconciliation import (
    calculate_actual_cash
)
from app.financial.models import CashMovementData


def test_completed_credit_cash_movement():

    movements = [
        CashMovementData(
            cash_movement_id=1,
            settlement_id=1,
            account_id=1,
            movement_type="SETTLEMENT",
            direction=CashMovementDirection.CREDIT,
            amount=Decimal("11000.00"),
            currency="INR",
            status=CashMovementStatus.COMPLETED
        )
    ]

    result = calculate_actual_cash(movements)

    assert result == Decimal("11000.00")

def test_failed_cash_movement_does_not_count():

    movements = [
        CashMovementData(
            cash_movement_id=1,
            settlement_id=1,
            account_id=1,
            movement_type="SETTLEMENT",
            direction=CashMovementDirection.CREDIT,
            amount=Decimal("11000.00"),
            currency="INR",
            status=CashMovementStatus.FAILED
        )
    ]

    result = calculate_actual_cash(movements)

    assert result == Decimal("0.00")

def test_pending_cash_movement_does_not_count():

    movements = [
        CashMovementData(
            cash_movement_id=1,
            settlement_id=1,
            account_id=1,
            movement_type="SETTLEMENT",
            direction=CashMovementDirection.CREDIT,
            amount=Decimal("11000.00"),
            currency="INR",
            status=CashMovementStatus.PENDING
        )
    ]

    result = calculate_actual_cash(movements)

    assert result == Decimal("0.00")

def test_multiple_completed_cash_movements_are_combined():

    movements = [
        CashMovementData(
            cash_movement_id=1,
            settlement_id=1,
            account_id=1,
            movement_type="SETTLEMENT",
            direction=CashMovementDirection.CREDIT,
            amount=Decimal("5000.00"),
            currency="INR",
            status=CashMovementStatus.COMPLETED
        ),
        CashMovementData(
            cash_movement_id=2,
            settlement_id=1,
            account_id=1,
            movement_type="SETTLEMENT",
            direction=CashMovementDirection.CREDIT,
            amount=Decimal("6000.00"),
            currency="INR",
            status=CashMovementStatus.COMPLETED
        )
    ]

    result = calculate_actual_cash(movements)

    assert result == Decimal("11000.00")

def test_completed_debit_is_negative():

    movements = [
        CashMovementData(
            cash_movement_id=1,
            settlement_id=1,
            account_id=1,
            movement_type="SETTLEMENT",
            direction=CashMovementDirection.DEBIT,
            amount=Decimal("3000.00"),
            currency="INR",
            status=CashMovementStatus.COMPLETED
        )
    ]

    result = calculate_actual_cash(movements)

    assert result == Decimal("-3000.00")

def test_no_cash_movements_results_in_zero():

    result = calculate_actual_cash([])

    assert result == Decimal("0.00")
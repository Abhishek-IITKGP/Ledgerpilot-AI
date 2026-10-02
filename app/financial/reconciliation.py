from decimal import Decimal

from app.financial.cash import calculate_cash_difference
from app.financial.models import ReconciliationDirection, ReconciliationResult, ReconciliationStatus


def reconcile_cash(
    expected_cash: Decimal,
    actual_cash: Decimal
) -> ReconciliationResult:

    if expected_cash < Decimal("0.00"):
        raise ValueError("Expected cash cannot be negative")
    if actual_cash < Decimal("0.00"):
        raise ValueError("Actual cash cannot be negative")

    difference = calculate_cash_difference(
        expected_cash,
        actual_cash
    )

    status = (
        ReconciliationStatus.MATCH.value
        if difference == Decimal("0.00")
        else ReconciliationStatus.MISMATCH.value
    )

    return ReconciliationResult(
        status=status,
        expected_cash=expected_cash,
        actual_cash=actual_cash,
        difference=difference,
        absolute_difference=abs(difference),
        reconciliation_direction=(
            ReconciliationDirection.EXECESS.value
            if difference > Decimal("0.00")
            else ReconciliationDirection.SHORTFALL.value
            if difference < Decimal("0.00")
            else ReconciliationDirection.MATCH.value
        )
    )    
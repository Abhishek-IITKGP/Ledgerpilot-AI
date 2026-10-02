from decimal import Decimal
from unittest.mock import Mock

from app.financial.models import (
    ReconciliationDirection,
    ReconciliationStatus,
    SettlementCashData
)

from app.financial.reconciliation_service import (
    ReconciliationService
)


def test_reconcile_settlement():

    # Arrange
    settlement_repository = Mock()
    cash_movement_repository = Mock()

    settlement_repository.get_cash_data.return_value = (
        SettlementCashData(
            settlement_id=1,
            expected_cash=Decimal("11000.00"),
            actual_cash=Decimal("0.00")
        )
    )

    cash_movement_repository.get_by_settlement.return_value = []

    service = ReconciliationService(
        settlement_repository,
        cash_movement_repository
    )

    # Act
    result = service.reconcile_settlement(1)

    # Assert
    assert result.status == ReconciliationStatus.MISMATCH.value

    assert (
        result.reconciliation_direction
        == ReconciliationDirection.SHORTFALL.value
    )

    assert result.expected_cash == Decimal("11000.00")

    assert result.actual_cash == Decimal("0.00")

    assert result.difference == Decimal("-11000.00")

    assert result.absolute_difference == Decimal("11000.00")

    settlement_repository.get_cash_data.assert_called_once_with(1)

    cash_movement_repository.get_by_settlement.assert_called_once_with(1)
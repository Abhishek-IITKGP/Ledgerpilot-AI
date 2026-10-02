import unittest
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


class TestReconciliationService(unittest.TestCase):

    def test_reconcile_settlement(self):

        repository = Mock()
        cash_movement_repository = Mock()
        cash_movement_repository.get_by_settlement.return_value = []

        repository.get_cash_data.return_value = SettlementCashData(
            settlement_id=1,
            expected_cash=Decimal("11000.00"),
            actual_cash=Decimal("0.00")
        )

        service = ReconciliationService(
            repository,
            cash_movement_repository
        )

        result = service.reconcile_settlement(1)

        self.assertEqual(
            result.status,
            ReconciliationStatus.MISMATCH.value
        )

        self.assertEqual(
            result.reconciliation_direction,
            ReconciliationDirection.SHORTFALL.value
        )

        self.assertEqual(
            result.difference,
            Decimal("-11000.00")
        )

        repository.get_cash_data.assert_called_once_with(1)
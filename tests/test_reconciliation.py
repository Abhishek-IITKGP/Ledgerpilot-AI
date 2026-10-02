import unittest
import decimal
from app.financial.reconciliation import reconcile_cash
from app.financial.models import ReconciliationStatus, ReconciliationDirection

class TestCashReconciliation(unittest.TestCase):
    def test_cash_matches(self):
        expected_cash = decimal.Decimal('1000.00')
        actual_cash = decimal.Decimal('1000.00')
        result = reconcile_cash(expected_cash, actual_cash)
        self.assertEqual(result.status, ReconciliationStatus.MATCH.value)
        self.assertEqual(result.reconciliation_direction, ReconciliationDirection.MATCH.value)
        self.assertEqual(result.difference, decimal.Decimal('0.00'))
    #Testing positive cash difference
    def test_positive_cash_difference(self):
        expected_cash = decimal.Decimal('1000.00')
        actual_cash = decimal.Decimal('1200.00')
        result = reconcile_cash(expected_cash, actual_cash)
        self.assertEqual(result.reconciliation_direction, ReconciliationDirection.EXECESS.value)
        self.assertEqual(result.status, ReconciliationStatus.MISMATCH.value)
        self.assertEqual(result.difference, decimal.Decimal('200.00'))

    #Testing shortfall in cash reconciliation
    def test_negative_cash_difference(self):
        expected_cash = decimal.Decimal('1000.00')
        actual_cash = decimal.Decimal('800.00')
        result = reconcile_cash(expected_cash, actual_cash)
        self.assertEqual(result.status, ReconciliationStatus.MISMATCH.value)
        self.assertEqual(result.difference, decimal.Decimal('-200.00'))
        self.assertEqual(result.reconciliation_direction, ReconciliationDirection.SHORTFALL.value)

    def test_actual_cash_negative(self):
        with self.assertRaises(ValueError):
            expected_cash = decimal.Decimal('1000.00')
            actual_cash = decimal.Decimal('-100.00')
            reconcile_cash(expected_cash, actual_cash)

    def test_expected_cash_negative(self):
        with self.assertRaises(ValueError):
            expected_cash = decimal.Decimal('-1000.00')
            actual_cash = decimal.Decimal('1000.00')
            reconcile_cash(expected_cash, actual_cash)
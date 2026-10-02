import unittest
from app.financial.cash import calculate_cash_difference

class TestCashCalculations(unittest.TestCase):
    def test_calculate_cash_difference_positive(self):
        expected_cash = 1000
        actual_cash = 1200
        result = calculate_cash_difference(expected_cash, actual_cash)
        self.assertEqual(result, 200)

    def test_calculate_cash_difference_negative(self):
        expected_cash = 1500
        actual_cash = 1200
        result = calculate_cash_difference(expected_cash, actual_cash)
        self.assertEqual(result, -300)

    def test_calculate_cash_difference_zero(self):
        expected_cash = 1000
        actual_cash = 1000
        result = calculate_cash_difference(expected_cash, actual_cash)
        self.assertEqual(result, 0)
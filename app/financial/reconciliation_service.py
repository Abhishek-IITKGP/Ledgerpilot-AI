from app.financial.reconciliation import reconcile_cash
from app.financial.cash_reconciliation import calculate_actual_cash


class ReconciliationService:

    def __init__(self, settlement_repository, cash_movement_repository):
        self.settlement_repository = settlement_repository
        self.cash_movement_repository = cash_movement_repository

    def reconcile_settlement(self, settlement_id: int):

        settlement_data = (
            self.settlement_repository
            .get_cash_data(settlement_id)
        )

        movements = (
        self.cash_movement_repository
        .get_by_settlement(settlement_id)
        )

        actual_cash = calculate_actual_cash(
        movements
        )

        return reconcile_cash(
            settlement_data.expected_cash,
            actual_cash
        )
from app.financial.models import ReconciliationStatus
from app.investigation.models import InvestigationCase, InvestigationContext


class InvestigationService:

    def __init__(
        self,
        settlement_repository,
        transaction_repository,
        order_repository,
        execution_repository,
        cash_movement_repository,
    ):
        self.settlement_repository = settlement_repository
        self.transaction_repository = transaction_repository
        self.order_repository = order_repository
        self.execution_repository = execution_repository
        self.cash_movement_repository = cash_movement_repository

    def create_case(self, settlement_id: int, reconciliation_result):
        if reconciliation_result.status == ReconciliationStatus.MATCH:
            return None

        return InvestigationCase(
            investigation_id=None,
            settlement_id=settlement_id,
            expected_cash=reconciliation_result.expected_cash,
            actual_cash=reconciliation_result.actual_cash,
            discrepancy=reconciliation_result.absolute_difference
        )

    def build_investigation_context(
        self,
        settlement_id: int,
        reconciliation_result,
    ) -> InvestigationContext:

        settlement = self.settlement_repository.get_investigation_data(
            settlement_id
        )

        transaction = self.transaction_repository.get_investigation_data(
            settlement.transaction_id
        )

        order = self.order_repository.get_investigation_data(
            transaction.order_id
        )

        executions = self.execution_repository.get_investigation_data(
            order.order_id
        )

        cash_movements = self.cash_movement_repository.get_by_settlement(
            settlement_id
        )

        case = self.create_case(
            settlement_id,
            reconciliation_result
        )

        return InvestigationContext(
            case=case,
            settlement=settlement,
            transaction=transaction,
            order=order,
            executions=executions,
            cash_movements=cash_movements,
        )
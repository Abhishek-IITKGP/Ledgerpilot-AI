from app.database.repositories.cash_movement_repository import (
    CashMovementRepository,
)
from app.database.repositories.execution_repository import ExecutionRepository
from app.database.repositories.investigation_repository import (
    InvestigationRepository,
)
from app.database.repositories.order_repository import OrderRepository
from app.database.repositories.policy_repository import PolicyRepository
from app.database.repositories.settlement_repository import SettlementRepository
from app.database.repositories.transaction_repository import (
    TransactionRepository,
)


class InvestigationReadOnlyTools:
    """Expose database reads needed by the investigation explanation agent."""

    def __init__(self, connection):
        self._investigations = InvestigationRepository(connection)
        self._settlements = SettlementRepository(connection)
        self._transactions = TransactionRepository(connection)
        self._orders = OrderRepository(connection)
        self._executions = ExecutionRepository(connection)
        self._cash_movements = CashMovementRepository(connection)
        self._policies = PolicyRepository(connection)

    def read_investigation(self, investigation_id: int):
        return self._investigations.get_by_id(investigation_id)

    def read_settlement(self, settlement_id: int):
        return self._settlements.get_investigation_data(settlement_id)

    def read_transaction(self, transaction_id: int):
        return self._transactions.get_investigation_data(transaction_id)

    def read_order(self, order_id: int):
        return self._orders.get_investigation_data(order_id)

    def read_executions(self, order_id: int):
        return self._executions.get_investigation_data(order_id)

    def read_cash_movements(self, settlement_id: int):
        return self._cash_movements.get_by_settlement(settlement_id)

    def read_approved_policies(self, search_terms: list[str], limit: int = 5):
        return self._policies.search_approved_chunks(search_terms, limit)
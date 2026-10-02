from app.investigation.investigation_engine import InvestigationEngine

from app.financial.models import ReconciliationStatus
class InvestigationWorkflow:

    def __init__(
        self,
        reconciliation_service,
        investigation_service,
        investigation_engine,
    ):
        self.reconciliation_service = reconciliation_service
        self.investigation_service = investigation_service
        self.investigation_engine = investigation_engine

    def investigate_settlement(self, settlement_id: int):

        reconciliation_result = (
            self.reconciliation_service.reconcile_settlement(
                settlement_id
            )
        )

        if reconciliation_result.status == ReconciliationStatus.MATCH:
            return None

        context = self.investigation_service.build_investigation_context(
            settlement_id,
            reconciliation_result,
        )

        return self.investigation_engine.investigate(context)
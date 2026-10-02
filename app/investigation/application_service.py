from app.financial.models import ReconciliationStatus
from app.investigation.investigation_engine import InvestigationEngine
from app.investigation.investigation_service import InvestigationService
from app.investigation.models import InvestigationFinding
from app.financial.models import InvestigationStatus
from app.investigation.investigation_workflow import InvestigationWorkflow


class InvestigationApplicationService:
    def __init__(
        self,
        workflow: InvestigationWorkflow,
        investigation_service: InvestigationService,
        investigation_engine: InvestigationEngine,
        case_repository,
        finding_repository,
        evidence_repository,
        investigation_repository,
        connection,
    ):
        self.workflow = workflow
        self.investigation_service = investigation_service
        self.investigation_engine = investigation_engine
        self.case_repository = case_repository
        self.finding_repository = finding_repository
        self.evidence_repository = evidence_repository
        self.investigation_repository = investigation_repository
        self.connection = connection

    def investigate_settlement(
        self,
        settlement_id: int,
        investigation_type: str = "CASH_DISCREPANCY",
        idempotency_key: str | None = None,
    ) -> InvestigationFinding | None:

        if idempotency_key is not None:
            existing_record = self.investigation_repository.get_by_request(
                settlement_id,
                investigation_type,
                idempotency_key,
            )

            if existing_record is not None:
                return existing_record.finding

        reconciliation_result = (
            self.workflow.reconciliation_service
            .reconcile_settlement(settlement_id)
        )

        if reconciliation_result.status == ReconciliationStatus.MATCH:
            return None

        context = self.investigation_service.build_investigation_context(
            settlement_id,
            reconciliation_result,
        )
        context.case.investigation_type = investigation_type
        context.case.idempotency_key = idempotency_key

        finding = self.investigation_engine.investigate(context)

        try:
            saved_case = self.case_repository.create(context.case)

            self.finding_repository.create(
                investigation_id=saved_case.investigation_id,
                finding=finding,
            )

            for evidence_text in finding.evidence:
                self.evidence_repository.create(
                    investigation_id=saved_case.investigation_id,
                    evidence_type="INVESTIGATION_ANALYSIS",
                    evidence_text=evidence_text,
                )

            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

        return finding

    def get_investigation(self, investigation_id: int):
        return self.investigation_repository.get_by_id(
            investigation_id
        )

    def update_investigation_status(
        self,
        investigation_id: int,
        status: InvestigationStatus,
    ):
        record = self.investigation_repository.update_investigation_status(
            investigation_id,
            status,
        )

        if record is not None:
            self.connection.commit()

        return record

    def list_investigations(
        self,
        settlement_id: int | None = None,
        status: str | None = None,
        severity: str | None = None,
        investigation_type: str | None = None,
    ):
        rows = self.investigation_repository.list_investigations(
            settlement_id=settlement_id,
            status=status,
            severity=severity,
            investigation_type=investigation_type,
        )

        return [
            {
                "investigation_id": row[0],
                "settlement_id": row[1],
                "investigation_type": row[2],
                "status": row[3],
                "discrepancy": str(row[4]),
                "severity": row[5],
                "created_at": row[6],
            }
            for row in rows
        ]
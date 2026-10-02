from app.financial.reconciliation_service import ReconciliationService
from app.investigation.investigation_engine import InvestigationEngine
from app.investigation.investigation_service import InvestigationService
from app.investigation.investigation_workflow import InvestigationWorkflow
from app.database.repositories.cash_movement_repository import CashMovementRepository
from app.database.repositories.execution_repository import ExecutionRepository
from app.database.repositories.order_repository import OrderRepository
from app.database.repositories.settlement_repository import SettlementRepository
from app.database.repositories.transaction_repository import TransactionRepository
from app.investigation.application_service import InvestigationApplicationService
from app.database.repositories.investigation_case_repository import InvestigationCaseRepository
from app.database.repositories.investigation_finding_repository import InvestigationFindingRepository
from app.database.repositories.investigation_evidence_repository import InvestigationEvidenceRepository
from app.database.repositories.investigation_repository import InvestigationRepository

def create_investigation_workflow(connection):
    reconciliation_service = ReconciliationService(
        settlement_repository=SettlementRepository(connection),
        cash_movement_repository=CashMovementRepository(connection),
    )

    investigation_service = InvestigationService(
        settlement_repository=SettlementRepository(connection),
        transaction_repository=TransactionRepository(connection),
        order_repository=OrderRepository(connection),
        execution_repository=ExecutionRepository(connection),
        cash_movement_repository=CashMovementRepository(connection),
    )

    investigation_engine = InvestigationEngine()

    return InvestigationWorkflow(
        reconciliation_service=reconciliation_service,
        investigation_service=investigation_service,
        investigation_engine=investigation_engine,
    )

def create_investigation_application_service(connection):
    workflow = create_investigation_workflow(connection)

    return InvestigationApplicationService(
        workflow=workflow,
        investigation_service=workflow.investigation_service,
        investigation_engine=workflow.investigation_engine,
        case_repository=InvestigationCaseRepository(connection),
        finding_repository=InvestigationFindingRepository(connection),
        evidence_repository=InvestigationEvidenceRepository(connection),
        investigation_repository=InvestigationRepository(connection),
        connection=connection,
    )
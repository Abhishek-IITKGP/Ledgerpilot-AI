from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID
from app.financial.models import CashMovementData


class InvestigationApprovalDecision(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REQUEST_CHANGES = "REQUEST_CHANGES"


@dataclass
class InvestigationCase:
    investigation_id: int | None
    settlement_id: int
    expected_cash: Decimal
    actual_cash: Decimal
    discrepancy: Decimal
    investigation_type: str = "CASH_DISCREPANCY"
    idempotency_key: str | None = None

@dataclass
class SettlementEvidence:

    settlement_id: int
    transaction_id: int
    settlement_type: str
    expected_cash: Decimal
    settled_cash: Decimal
    status: str
    failure_reason: str | None

@dataclass
class TransactionEvidence:

    transaction_id: int
    transaction_type: str
    gross_amount: Decimal
    fee_amount: Decimal
    net_amount: Decimal
    status: str
    order_id : int

@dataclass
class ExecutionEvidence:

    execution_id: int
    order_id: int
    execution_quantity: int
    execution_price: Decimal
    execution_time: datetime
    status: str

@dataclass
class OrderEvidence:

    order_id: int
    account_id: int
    security_id: int
    side: str
    order_type: str
    quantity: int
    limit_price: Decimal | None
    status: str
    created_at: datetime

@dataclass
class InvestigationContext:
    
    case : InvestigationCase
    settlement : SettlementEvidence
    transaction : TransactionEvidence
    order : OrderEvidence
    executions : list[ExecutionEvidence]
    cash_movements: list[CashMovementData]


@dataclass
class InvestigationFinding:
    root_causes: list[str]
    impact: Decimal
    severity: str
    evidence: list[str]
    recommended_action: str | None

@dataclass
class InvestigationRecord:
    case: InvestigationCase
    status: str
    created_at: datetime
    updated_at: datetime
    finding: InvestigationFinding | None


@dataclass
class InvestigationApprovalEvent:
    approval_event_id: int
    investigation_id: int
    actor_user_id: int
    explanation_run_id: UUID | None
    event_type: str
    previous_status: str
    new_status: str
    comment: str
    created_at: datetime
from dataclasses import dataclass, field
from uuid import UUID

from app.financial.models import CashMovementData
from app.investigation.models import (
    ExecutionEvidence,
    InvestigationRecord,
    OrderEvidence,
    SettlementEvidence,
    TransactionEvidence,
)


@dataclass
class InvestigationExplanation:
    investigation_id: int
    summary: str
    business_impact: str
    root_cause_explanations: list[str]
    evidence: list[str]
    confidence: str
    recommended_action: str | None
    requires_human_review: bool
    provider: str
    preventive_actions: list[str] = field(default_factory=list)
    policy_references: list[str] = field(default_factory=list)
    audit_run_id: UUID | None = None


@dataclass
class RetrievedPolicyChunk:
    reference: str
    title: str
    source_name: str
    content: str


@dataclass
class InvestigationExplanationContext:
    investigation: InvestigationRecord
    settlement: SettlementEvidence
    transaction: TransactionEvidence
    order: OrderEvidence
    executions: list[ExecutionEvidence]
    cash_movements: list[CashMovementData]
    policy_guidance: list[RetrievedPolicyChunk] = field(default_factory=list)

    def to_prompt_data(self) -> dict[str, object]:
        case = self.investigation.case
        finding = self.investigation.finding

        if finding is None:
            raise ValueError("Investigation does not contain a finding")

        return {
            "finding": {
                "expected_cash": str(case.expected_cash),
                "actual_cash": str(case.actual_cash),
                "discrepancy": str(case.discrepancy),
                "severity": finding.severity,
                "deterministic_root_causes": finding.root_causes,
                "stored_evidence": finding.evidence,
                "deterministic_recommended_action": (
                    finding.recommended_action
                ),
            },
            "settlement": {
                "settlement_type": self.settlement.settlement_type,
                "expected_cash": str(self.settlement.expected_cash),
                "settled_cash": str(self.settlement.settled_cash),
                "status": self.settlement.status,
                "failure_reason": self.settlement.failure_reason,
            },
            "transaction": {
                "transaction_type": self.transaction.transaction_type,
                "gross_amount": str(self.transaction.gross_amount),
                "fee_amount": str(self.transaction.fee_amount),
                "net_amount": str(self.transaction.net_amount),
                "status": self.transaction.status,
            },
            "order": {
                "side": self.order.side,
                "order_type": self.order.order_type,
                "quantity": self.order.quantity,
                "limit_price": (
                    str(self.order.limit_price)
                    if self.order.limit_price is not None
                    else None
                ),
                "status": self.order.status,
            },
            "executions": [
                {
                    "quantity": execution.execution_quantity,
                    "price": str(execution.execution_price),
                    "time": execution.execution_time.isoformat(),
                    "status": execution.status,
                }
                for execution in self.executions
            ],
            "cash_movements": [
                {
                    "movement_type": movement.movement_type,
                    "direction": movement.direction.value,
                    "amount": str(movement.amount),
                    "currency": movement.currency,
                    "status": movement.status.value,
                }
                for movement in self.cash_movements
            ],
            "approved_policy_guidance": [
                {
                    "reference": policy.reference,
                    "title": policy.title,
                    "source_name": policy.source_name,
                    "content": policy.content,
                }
                for policy in self.policy_guidance
            ],
        }

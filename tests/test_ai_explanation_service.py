import hashlib
import json
from datetime import datetime
from decimal import Decimal

import pytest

from app.ai.agent import InvestigationExplanationAgent
from app.ai.explanation_service import (
    DeterministicExplanationProvider,
)
from app.ai.models import (
    InvestigationExplanationContext,
    RetrievedPolicyChunk,
)
from app.ai.tools import InvestigationReadOnlyTools
from app.financial.models import (
    CashMovementData,
    CashMovementDirection,
    CashMovementStatus,
)
from app.investigation.models import (
    InvestigationCase,
    ExecutionEvidence,
    InvestigationFinding,
    InvestigationRecord,
    OrderEvidence,
    SettlementEvidence,
    TransactionEvidence,
)


def make_record(severity="HIGH", evidence=None):
    return InvestigationRecord(
        case=InvestigationCase(
            investigation_id=42,
            settlement_id=227,
            expected_cash=Decimal("11000.00"),
            actual_cash=Decimal("0.00"),
            discrepancy=Decimal("11000.00"),
        ),
        status="OPEN",
        created_at=datetime(2026, 1, 1),
        updated_at=datetime(2026, 1, 1),
        finding=InvestigationFinding(
            root_causes=["CASH_MOVEMENT_MISMATCH"],
            impact=Decimal("11000.00"),
            severity=severity,
            evidence=evidence or ["No completed cash movement was recorded"],
            recommended_action="Review the cash movement discrepancy.",
        ),
    )


def make_context(severity="HIGH", evidence=None):
    return InvestigationExplanationContext(
        investigation=make_record(severity, evidence),
        settlement=SettlementEvidence(
            settlement_id=227,
            transaction_id=19,
            settlement_type="CASH_RECEIVABLE",
            expected_cash=Decimal("11000.00"),
            settled_cash=Decimal("0.00"),
            status="FAILED",
            failure_reason="INVALID_SETTLEMENT_INSTRUCTION",
        ),
        transaction=TransactionEvidence(
            transaction_id=19,
            transaction_type="SELL",
            gross_amount=Decimal("11000.00"),
            fee_amount=Decimal("0.00"),
            net_amount=Decimal("11000.00"),
            status="COMPLETED",
            order_id=61,
        ),
        order=OrderEvidence(
            order_id=61,
            account_id=4,
            security_id=9,
            side="SELL",
            order_type="MARKET",
            quantity=20,
            limit_price=None,
            status="COMPLETED",
            created_at=datetime(2026, 1, 1),
        ),
        executions=[
            ExecutionEvidence(
                execution_id=73,
                order_id=61,
                execution_quantity=20,
                execution_price=Decimal("550.00"),
                execution_time=datetime(2026, 1, 1),
                status="COMPLETED",
            )
        ],
        cash_movements=[
            CashMovementData(
                cash_movement_id=88,
                settlement_id=227,
                account_id=4,
                movement_type="SETTLEMENT",
                direction=CashMovementDirection.CREDIT,
                amount=Decimal("11000.00"),
                currency="INR",
                status=CashMovementStatus.FAILED,
            )
        ],
        policy_guidance=[
            RetrievedPolicyChunk(
                reference="SETTLEMENT_FAILURE_REVIEW@demo-v1#chunk-0",
                title="Sample: Settlement Failure Review",
                source_name="FinSight demonstration policy",
                content="Verify the settlement instruction before reprocessing.",
            )
        ],
    )


class FakeTools:
    def __init__(self, context, missing_investigation=False):
        self.context = context
        self.missing_investigation = missing_investigation
        self.calls = []

    def read_investigation(self, investigation_id):
        self.calls.append(("investigation", investigation_id))
        if self.missing_investigation:
            return None
        return self.context.investigation

    def read_settlement(self, settlement_id):
        self.calls.append(("settlement", settlement_id))
        return self.context.settlement

    def read_transaction(self, transaction_id):
        self.calls.append(("transaction", transaction_id))
        return self.context.transaction

    def read_order(self, order_id):
        self.calls.append(("order", order_id))
        return self.context.order

    def read_executions(self, order_id):
        self.calls.append(("executions", order_id))
        return self.context.executions

    def read_cash_movements(self, settlement_id):
        self.calls.append(("cash_movements", settlement_id))
        return self.context.cash_movements

    def read_approved_policies(self, search_terms, limit=5):
        self.calls.append(("policies", search_terms, limit))
        return self.context.policy_guidance


class CapturingProvider:
    name = "capturing-provider"
    model = "test-model"

    def explain(self, context):
        self.context = context
        return DeterministicExplanationProvider().explain(context)


class FakeAuditRepository:
    def __init__(self):
        self.runs = []

    def record_run(self, **run):
        self.runs.append(run)


class FailingProvider:
    name = "failing-provider"
    model = "test-model"

    def explain(self, context):
        raise ValueError("private provider response text")


def test_agent_gathers_linked_records_before_explaining():
    context = make_context()
    tools = FakeTools(context)
    provider = CapturingProvider()
    audit_repository = FakeAuditRepository()
    agent = InvestigationExplanationAgent(
        tools,
        provider,
        audit_repository,
    )

    result = agent.explain_investigation(42, requested_by_user_id=3)

    assert result.investigation_id == 42
    assert tools.calls == [
        ("investigation", 42),
        ("settlement", 227),
        ("transaction", 19),
        ("order", 61),
        ("executions", 61),
        ("cash_movements", 227),
        (
            "policies",
            ["cash", "instruction", "invalid", "mismatch", "movement", "settlement"],
            5,
        ),
    ]
    prompt_data = provider.context.to_prompt_data()
    assert prompt_data["settlement"]["failure_reason"] == (
        "INVALID_SETTLEMENT_INSTRUCTION"
    )
    assert prompt_data["cash_movements"][0]["status"] == "FAILED"
    assert prompt_data["approved_policy_guidance"][0]["reference"] == (
        "SETTLEMENT_FAILURE_REVIEW@demo-v1#chunk-0"
    )
    assert len(audit_repository.runs) == 1
    audit_run = audit_repository.runs[0]
    assert audit_run["status"] == "SUCCEEDED"
    assert audit_run["requested_by_user_id"] == 3
    assert audit_run["model"] == "test-model"
    assert audit_run["input_sha256"] == hashlib.sha256(
        json.dumps(
            prompt_data,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    assert audit_run["output_snapshot"]["investigation_id"] == 42


def test_agent_records_safe_failure_category_without_exception_text():
    audit_repository = FakeAuditRepository()
    agent = InvestigationExplanationAgent(
        FakeTools(make_context()),
        FailingProvider(),
        audit_repository,
    )

    with pytest.raises(ValueError, match="private provider"):
        agent.explain_investigation(42, requested_by_user_id=3)

    assert len(audit_repository.runs) == 1
    audit_run = audit_repository.runs[0]
    assert audit_run["status"] == "FAILED"
    assert audit_run["error_category"] == "INVALID_PROVIDER_RESPONSE"
    assert audit_run.get("output_snapshot") is None
    assert "private provider response text" not in str(audit_run)


def test_agent_stops_when_investigation_is_missing():
    tools = FakeTools(make_context(), missing_investigation=True)
    audit_repository = FakeAuditRepository()
    agent = InvestigationExplanationAgent(
        tools,
        CapturingProvider(),
        audit_repository,
    )

    assert agent.explain_investigation(999, requested_by_user_id=3) is None
    assert tools.calls == [("investigation", 999)]
    assert audit_repository.runs == []


def test_read_only_tools_expose_only_read_methods():
    public_methods = [
        name
        for name, value in vars(InvestigationReadOnlyTools).items()
        if callable(value) and not name.startswith("_")
    ]

    assert public_methods
    assert all(name.startswith("read_") for name in public_methods)


def test_explanation_is_grounded_in_persisted_finding():
    explanation = DeterministicExplanationProvider().explain(make_context())

    assert explanation.investigation_id == 42
    assert "11000.00" in explanation.summary
    assert explanation.evidence == ["No completed cash movement was recorded"]
    assert explanation.confidence == "HIGH"
    assert explanation.requires_human_review is True
    assert explanation.provider == "deterministic-demo-provider"
    assert explanation.policy_references == [
        "SETTLEMENT_FAILURE_REVIEW@demo-v1#chunk-0"
    ]


def test_explanation_returns_none_for_missing_investigation():
    tools = FakeTools(make_context(), missing_investigation=True)
    audit_repository = FakeAuditRepository()
    agent = InvestigationExplanationAgent(
        tools,
        DeterministicExplanationProvider(),
        audit_repository,
    )

    assert agent.explain_investigation(999, requested_by_user_id=3) is None


def test_provider_rejects_investigation_without_finding():
    context = make_context()
    context.investigation.finding = None

    with pytest.raises(ValueError, match="persisted finding"):
        DeterministicExplanationProvider().explain(context)

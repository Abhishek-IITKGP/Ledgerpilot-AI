import json
from datetime import datetime
from decimal import Decimal
from urllib.error import HTTPError

import pytest

from app.ai.models import (
    InvestigationExplanationContext,
    RetrievedPolicyChunk,
)
from app.ai.llm_provider import (
    LLMExplanationProvider,
    LLMProviderUnavailableError,
)
from app.investigation.models import (
    OrderEvidence,
    SettlementEvidence,
    TransactionEvidence,
)
from app.investigation.models import (
    InvestigationCase,
    InvestigationFinding,
    InvestigationRecord,
)


def make_record():
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
            severity="HIGH",
            evidence=["No completed cash movement was recorded"],
            recommended_action="Review the cash movement discrepancy.",
        ),
    )


def make_context():
    return InvestigationExplanationContext(
        investigation=make_record(),
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
        executions=[],
        cash_movements=[],
        policy_guidance=[
            RetrievedPolicyChunk(
                reference="SETTLEMENT_FAILURE_REVIEW@demo-v1#chunk-0",
                title="Sample: Settlement Failure Review",
                source_name="FinSight demonstration policy",
                content="Verify the settlement instruction before reprocessing.",
            )
        ],
    )


def test_llm_provider_sends_grounded_payload_and_parses_response():
    captured = {}

    def fake_request(request):
        captured["authorization"] = request.get_header("Authorization")
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "summary": "The cash movement is missing.",
                                    "business_impact": "11000.00 remains unresolved.",
                                    "root_cause_explanations": [
                                        "The cash posting did not complete."
                                    ],
                                    "confidence": "HIGH",
                                    "recommended_action": "Review the posting queue.",
                                    "requires_human_review": True,
                                    "preventive_actions": [
                                        "Validate instructions before reprocessing."
                                    ],
                                    "policy_references": [
                                        "SETTLEMENT_FAILURE_REVIEW@demo-v1#chunk-0"
                                    ],
                                }
                            )
                        }
                    }
                ]
            }
        ).encode("utf-8")

    provider = LLMExplanationProvider(
        api_key="test-key",
        model="test-model",
        endpoint="https://example.test/chat/completions",
        request=fake_request,
    )

    explanation = provider.explain(make_context())

    assert captured["authorization"] == "Bearer test-key"
    assert captured["payload"]["model"] == "test-model"
    assert captured["payload"]["temperature"] == 0
    user_payload = json.loads(captured["payload"]["messages"][1]["content"])
    assert user_payload["finding"]["discrepancy"] == "11000.00"
    assert user_payload["finding"]["stored_evidence"] == [
        "No completed cash movement was recorded"
    ]
    assert user_payload["settlement"]["failure_reason"] == (
        "INVALID_SETTLEMENT_INSTRUCTION"
    )
    assert user_payload["approved_policy_guidance"][0]["reference"] == (
        "SETTLEMENT_FAILURE_REVIEW@demo-v1#chunk-0"
    )
    assert "account_id" not in user_payload["order"]
    assert "security_id" not in user_payload["order"]
    assert explanation.summary == "The cash movement is missing."
    assert explanation.evidence == ["No completed cash movement was recorded"]
    assert explanation.provider == "openai-compatible-llm"
    assert explanation.preventive_actions == [
        "Validate instructions before reprocessing."
    ]
    assert explanation.policy_references == [
        "SETTLEMENT_FAILURE_REVIEW@demo-v1#chunk-0"
    ]


def test_llm_provider_rejects_invalid_response():
    def fake_request(request):
        return json.dumps(
            {
                "choices": [
                    {"message": {"content": '{"confidence": "UNKNOWN"}'}}
                ]
            }
        ).encode("utf-8")

    provider = LLMExplanationProvider(
        api_key="test-key",
        model="test-model",
        request=fake_request,
        max_retries=0,
    )

    with pytest.raises(ValueError, match="invalid explanation"):
        provider.explain(make_context())


def test_llm_provider_rejects_policy_reference_not_in_context():
    def fake_request(request):
        return json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "summary": "A cash movement is missing.",
                                    "business_impact": "Cash remains unresolved.",
                                    "root_cause_explanations": [
                                        "The posting failed."
                                    ],
                                    "confidence": "HIGH",
                                    "recommended_action": None,
                                    "requires_human_review": True,
                                    "preventive_actions": [
                                        "Validate settlement instructions."
                                    ],
                                    "policy_references": [
                                        "MADE_UP_POLICY@v1#chunk-0"
                                    ],
                                }
                            )
                        }
                    }
                ]
            }
        ).encode("utf-8")

    provider = LLMExplanationProvider(
        api_key="test-key",
        model="test-model",
        request=fake_request,
        max_retries=0,
    )

    with pytest.raises(ValueError, match="invalid explanation"):
        provider.explain(make_context())


def test_llm_provider_translates_upstream_outage():
    def fake_request(request):
        raise HTTPError(
            request.full_url,
            503,
            "Service Unavailable",
            hdrs=None,
            fp=None,
        )

    provider = LLMExplanationProvider(
        api_key="test-key",
        model="test-model",
        request=fake_request,
    )

    with pytest.raises(LLMProviderUnavailableError) as error:
        provider.explain(make_context())

    assert error.value.status_code == 503


def test_llm_provider_retries_transient_outage():
    calls = 0

    def fake_request(request):
        nonlocal calls
        calls += 1
        if calls < 3:
            raise HTTPError(
                request.full_url,
                503,
                "Service Unavailable",
                hdrs=None,
                fp=None,
            )

        return json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "summary": "Recovered explanation.",
                                    "business_impact": "No new impact.",
                                    "root_cause_explanations": [
                                        "The provider recovered."
                                    ],
                                    "confidence": "HIGH",
                                    "recommended_action": None,
                                    "requires_human_review": True,
                                }
                            )
                        }
                    }
                ]
            }
        ).encode("utf-8")

    provider = LLMExplanationProvider(
        api_key="test-key",
        model="test-model",
        request=fake_request,
        max_retries=2,
        retry_delay_seconds=0,
    )

    explanation = provider.explain(make_context())

    assert calls == 3
    assert explanation.summary == "Recovered explanation."

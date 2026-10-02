from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.api.routes import ai as ai_routes
from app.api.routes.ai import (
    get_ai_audit_repository,
    get_db_connection,
)
from app.ai.llm_provider import LLMProviderUnavailableError
from app.auth.security import get_current_user
from app.auth.user_repository import AuthenticatedUser
from app.database.repositories.investigation_case_repository import (
    InvestigationCaseRepository,
)
from app.database.repositories.investigation_evidence_repository import (
    InvestigationEvidenceRepository,
)
from app.database.repositories.investigation_finding_repository import (
    InvestigationFindingRepository,
)
from app.investigation.models import InvestigationCase, InvestigationFinding


@pytest.fixture(autouse=True)
def authenticated_api_user(monkeypatch):
    class FakeAuditRepository:
        def __init__(self):
            self.runs = []
            self.run_id = uuid4()

        def record_run(self, **run):
            self.runs.append(run)
            return self.run_id

    audit_repository = FakeAuditRepository()
    monkeypatch.setenv("AI_PROVIDER", "mock")
    app.dependency_overrides[get_ai_audit_repository] = (
        lambda: audit_repository
    )
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        user_id=3,
        username="admin.one",
        email="admin@example.com",
        is_active=True,
        role="ADMINISTRATOR",
    )
    yield audit_repository
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_ai_audit_repository, None)


@pytest.fixture
def test_customer(db_connection):
    email = f"ai-api-test-{uuid4()}@example.com"
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO financial.customers (
                first_name,
                last_name,
                email,
                phone,
                status
            )
            VALUES ('AI API', 'Test', %s, '9999999997', 'ACTIVE')
            RETURNING customer_id
            """,
            (email,),
        )
        return cursor.fetchone()[0]


def test_ai_explanation_endpoint_uses_persisted_investigation(
    db_connection,
    test_settlement,
    authenticated_api_user,
):
    case = InvestigationCaseRepository(db_connection).create(
        InvestigationCase(
            investigation_id=None,
            settlement_id=test_settlement,
            expected_cash=Decimal("11000.00"),
            actual_cash=Decimal("0.00"),
            discrepancy=Decimal("11000.00"),
        )
    )
    finding = InvestigationFinding(
        root_causes=["CASH_MOVEMENT_MISMATCH"],
        impact=Decimal("11000.00"),
        severity="HIGH",
        evidence=["No completed cash movement was recorded"],
        recommended_action="Review the cash movement discrepancy.",
    )
    InvestigationFindingRepository(db_connection).create(
        case.investigation_id,
        finding,
    )
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO ai.policy_documents (
                document_key,
                title,
                source_name,
                version,
                publication_status,
                approved_by_user_id,
                approved_at
            )
            VALUES (
                'AI_API_TEST_POLICY',
                'AI API test policy',
                'Automated test fixture',
                'test-v1',
                'APPROVED',
                3,
                CURRENT_TIMESTAMP
            )
            RETURNING document_id
            """
        )
        policy_document_id = cursor.fetchone()[0]
        cursor.execute(
            """
            INSERT INTO ai.policy_chunks (
                document_id,
                chunk_index,
                content,
                keywords
            )
            VALUES (
                %s,
                0,
                'Before reprocessing a failed settlement, verify its instruction and cash movement.',
                ARRAY['settlement', 'instruction', 'cash', 'movement', 'failed', 'mismatch']
            )
            """,
            (policy_document_id,),
        )
    InvestigationEvidenceRepository(db_connection).create(
        investigation_id=case.investigation_id,
        evidence_type="FINANCIAL_RECORD",
        source_table="financial.settlements",
        source_record_id=test_settlement,
        evidence_text="No completed cash movement was recorded",
    )
    app.dependency_overrides[get_db_connection] = lambda: db_connection

    try:
        response = TestClient(app).post(
            f"/ai/investigations/{case.investigation_id}/explanation"
        )

        assert response.status_code == 200
        response_data = response.json()
        policy_references = response_data.pop("policy_references")
        assert response_data.pop("audit_run_id") == str(
            authenticated_api_user.run_id
        )
        assert response_data == {
            "investigation_id": case.investigation_id,
            "summary": (
                f"Investigation {case.investigation_id} found a HIGH "
                f"financial discrepancy of 11000.00 for settlement "
                f"{test_settlement}."
            ),
            "business_impact": (
                "The expected cash differs from actual cash by 11000.00. "
                "This finding should be reviewed before settlement reprocessing."
            ),
            "root_cause_explanations": [
                "The deterministic investigation classified this cause as "
                "CASH_MOVEMENT_MISMATCH."
            ],
            "evidence": ["No completed cash movement was recorded"],
            "confidence": "HIGH",
            "recommended_action": "Review the cash movement discrepancy.",
            "requires_human_review": True,
            "provider": "deterministic-demo-provider",
            "preventive_actions": [],
        }
        assert "AI_API_TEST_POLICY@test-v1#chunk-0" in policy_references
        assert len(authenticated_api_user.runs) == 1
        audit_run = authenticated_api_user.runs[0]
        assert audit_run["investigation_id"] == case.investigation_id
        assert audit_run["requested_by_user_id"] == 3
        assert audit_run["provider"] == "deterministic-demo-provider"
        assert audit_run["status"] == "SUCCEEDED"
        assert len(audit_run["input_sha256"]) == 64
        assert audit_run["input_snapshot"]["approved_policy_guidance"]

        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT status, expected_cash_amount, settled_cash_amount
                FROM financial.settlements
                WHERE settlement_id = %s
                """,
                (test_settlement,),
            )
            settlement_after = cursor.fetchone()
            cursor.execute(
                """
                SELECT status
                FROM investigation.cases
                WHERE investigation_id = %s
                """,
                (case.investigation_id,),
            )
            investigation_after = cursor.fetchone()

        assert settlement_after == ("FAILED", Decimal("11000.00"), Decimal("0.00"))
        assert investigation_after == ("OPEN",)
    finally:
        app.dependency_overrides.clear()


def test_ai_provider_failure_returns_generic_internal_error(
    db_connection,
    monkeypatch,
):
    def failing_service(connection, audit_repository):
        raise LLMProviderUnavailableError(
            "provider details must not reach the client",
            status_code=503,
        )

    monkeypatch.setattr(
        ai_routes,
        "create_explanation_service",
        failing_service,
    )
    app.dependency_overrides[get_db_connection] = lambda: db_connection

    try:
        response = TestClient(app).post(
            "/ai/investigations/7/explanation"
        )

        assert response.status_code == 500
        assert response.json() == {"detail": "Internal Server Error"}
    finally:
        app.dependency_overrides.clear()

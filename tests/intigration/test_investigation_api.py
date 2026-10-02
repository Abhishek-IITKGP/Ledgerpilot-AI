from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.api.routes.investigation import get_db_connection
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
def authenticated_api_user():
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        user_id=3,
        username="admin.one",
        email="admin@example.com",
        is_active=True,
        role="ADMINISTRATOR",
    )
    yield
    app.dependency_overrides.pop(get_current_user, None)


def test_gs001_investigation_api(db_connection):
    app.dependency_overrides[get_db_connection] = (
        lambda: db_connection
    )

    try:
        client = TestClient(app)

        response = client.post(
            "/investigations/settlements/227",
            json={
                "investigation_type": "CASH_DISCREPANCY",
                "idempotency_key": "gs001-api-test",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["root_causes"] == [
            "INVALID_SETTLEMENT_INSTRUCTION",
            "CASH_MOVEMENT_MISMATCH",
        ]

        assert data["impact"] == "11000.00"
        assert data["severity"] == "HIGH"

        assert (
            "No completed cash movement was recorded"
            in data["evidence"]
        )

        assert data["recommended_action"] == (
            "Review the settlement instruction and investigate the "
            "cash movement discrepancy before reprocessing settlement."
        )

    finally:
        app.dependency_overrides.clear()


def test_get_persisted_investigation_api(
    db_connection,
    test_settlement,
):
    saved_case = InvestigationCaseRepository(db_connection).create(
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
        recommended_action=None,
    )

    InvestigationFindingRepository(db_connection).create(
        saved_case.investigation_id,
        finding,
    )
    InvestigationEvidenceRepository(db_connection).create(
        investigation_id=saved_case.investigation_id,
        evidence_type="FINANCIAL_RECORD",
        source_table="financial.settlements",
        source_record_id=test_settlement,
        evidence_text="No completed cash movement was recorded",
    )

    app.dependency_overrides[get_db_connection] = (
        lambda: db_connection
    )

    try:
        response = TestClient(app).get(
            f"/investigations/{saved_case.investigation_id}"
        )

        assert response.status_code == 200
        assert response.json() == {
            "investigation_id": saved_case.investigation_id,
            "settlement_id": test_settlement,
            "expected_cash": "11000.00",
            "actual_cash": "0.00",
            "discrepancy": "11000.00",
            "status": "OPEN",
            "created_at": response.json()["created_at"],
            "updated_at": response.json()["updated_at"],
            "finding": {
                "root_causes": ["CASH_MOVEMENT_MISMATCH"],
                "impact": "11000.00",
                "severity": "HIGH",
                "evidence": [
                    "No completed cash movement was recorded"
                ],
                "recommended_action": None,
            },
        }
    finally:
        app.dependency_overrides.clear()

def test_investigation_api_returns_404_for_missing_settlement(
    db_connection,
):
    app.dependency_overrides[get_db_connection] = (
        lambda: db_connection
    )

    try:
        client = TestClient(app)

        response = client.post(
            "/investigations/settlements/999999999",
            json={
                "investigation_type": "CASH_DISCREPANCY",
                "idempotency_key": "missing-settlement-test",
            },
        )

        assert response.status_code == 404
        assert response.json() == {
            "detail": "Settlement 999999999 not found"
        }

    finally:
        app.dependency_overrides.clear()


def test_repeated_investigation_request_is_idempotent(
    db_connection,
):
    app.dependency_overrides[get_db_connection] = (
        lambda: db_connection
    )

    request = {
        "investigation_type": "CASH_DISCREPANCY",
        "idempotency_key": "gs001-repeat-test",
    }

    try:
        client = TestClient(app)

        first_response = client.post(
            "/investigations/settlements/227",
            json=request,
        )
        second_response = client.post(
            "/investigations/settlements/227",
            json=request,
        )

        assert first_response.status_code == 200
        assert second_response.status_code == 200
        assert second_response.json() == first_response.json()

        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM investigation.cases
                WHERE settlement_id = %s
                  AND investigation_type = %s
                  AND idempotency_key = %s
                """,
                (227, request["investigation_type"], request["idempotency_key"]),
            )
            case_count = cursor.fetchone()[0]

        assert case_count == 1
    finally:
        app.dependency_overrides.clear()


def test_list_investigations_supports_filters(
    db_connection,
    test_settlement,
):
    case_repository = InvestigationCaseRepository(db_connection)
    finding_repository = InvestigationFindingRepository(db_connection)

    high_case = case_repository.create(
        InvestigationCase(
            investigation_id=None,
            settlement_id=test_settlement,
            expected_cash=Decimal("11000.00"),
            actual_cash=Decimal("0.00"),
            discrepancy=Decimal("11000.00"),
            investigation_type="CASH_DISCREPANCY",
            idempotency_key="list-high-test",
        )
    )
    low_case = case_repository.create(
        InvestigationCase(
            investigation_id=None,
            settlement_id=test_settlement,
            expected_cash=Decimal("100.00"),
            actual_cash=Decimal("90.00"),
            discrepancy=Decimal("10.00"),
            investigation_type="SETTLEMENT_REVIEW",
            idempotency_key="list-low-test",
        )
    )

    finding_repository.create(
        high_case.investigation_id,
        InvestigationFinding(
            root_causes=["CASH_MOVEMENT_MISMATCH"],
            impact=Decimal("11000.00"),
            severity="HIGH",
            evidence=[],
            recommended_action=None,
        ),
    )
    finding_repository.create(
        low_case.investigation_id,
        InvestigationFinding(
            root_causes=["AMOUNT_MISMATCH"],
            impact=Decimal("10.00"),
            severity="LOW",
            evidence=[],
            recommended_action=None,
        ),
    )

    app.dependency_overrides[get_db_connection] = (
        lambda: db_connection
    )

    try:
        response = TestClient(app).get(
            "/investigations/",
            params={
                "settlement_id": test_settlement,
                "severity": "HIGH",
                "investigation_type": "CASH_DISCREPANCY",
                "status": "OPEN",
            },
        )

        assert response.status_code == 200
        assert response.json() == [
            {
                "investigation_id": high_case.investigation_id,
                "settlement_id": test_settlement,
                "investigation_type": "CASH_DISCREPANCY",
                "status": "OPEN",
                "discrepancy": "11000.00",
                "severity": "HIGH",
                "created_at": response.json()[0]["created_at"],
            }
        ]
    finally:
        app.dependency_overrides.clear()


def test_analyst_cannot_update_investigation_status(db_connection):
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        user_id=1,
        username="analyst.one",
        email="analyst@example.com",
        is_active=True,
        role="ANALYST",
    )

    try:
        response = TestClient(app).put(
            "/investigations/999999999/",
            params={"status": "CLOSED"},
        )

        assert response.status_code == 403
        assert response.json() == {
            "detail": "Insufficient permissions"
        }
    finally:
        app.dependency_overrides.clear()


def test_analyst_can_read_investigation_detail(
    db_connection,
    test_settlement,
):
    saved_case = InvestigationCaseRepository(db_connection).create(
        InvestigationCase(
            investigation_id=None,
            settlement_id=test_settlement,
            expected_cash=Decimal("11000.00"),
            actual_cash=Decimal("0.00"),
            discrepancy=Decimal("11000.00"),
        )
    )

    app.dependency_overrides[get_db_connection] = (
        lambda: db_connection
    )
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        user_id=1,
        username="analyst.one",
        email="analyst@example.com",
        is_active=True,
        role="ANALYST",
    )

    try:
        response = TestClient(app).get(
            f"/investigations/{saved_case.investigation_id}"
        )

        assert response.status_code == 200
        assert response.json()["investigation_id"] == (
            saved_case.investigation_id
        )
    finally:
        app.dependency_overrides.clear()
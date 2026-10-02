from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.api.routes.investigation import get_db_connection
from app.auth.security import get_current_user
from app.auth.user_repository import AuthenticatedUser
from app.database.repositories.investigation_case_repository import (
    InvestigationCaseRepository,
)
from app.database.repositories.investigation_finding_repository import (
    InvestigationFindingRepository,
)
from app.investigation.models import InvestigationCase, InvestigationFinding


class NonCommittingConnection:
    def __init__(self, connection):
        self.connection = connection

    def cursor(self):
        return self.connection.cursor()

    def commit(self):
        return None

    def rollback(self):
        return None


@pytest.fixture
def approval_api(db_connection):
    request_connection = NonCommittingConnection(db_connection)
    app.dependency_overrides[get_db_connection] = lambda: request_connection

    def set_user(user_id, role):
        app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
            user_id=user_id,
            username=f"test-{role.lower()}",
            email=f"test-{role.lower()}@example.com",
            is_active=True,
            role=role,
        )

    try:
        yield TestClient(app), set_user
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def test_customer(db_connection):
    email = f"approval-test-{uuid4()}@example.com"
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
            VALUES ('Approval', 'Test', %s, '9999999998', 'ACTIVE')
            RETURNING customer_id
            """,
            (email,),
        )
        return cursor.fetchone()[0]


def create_reviewable_case(db_connection, settlement_id):
    case = InvestigationCaseRepository(db_connection).create(
        InvestigationCase(
            investigation_id=None,
            settlement_id=settlement_id,
            expected_cash=Decimal("11000.00"),
            actual_cash=Decimal("0.00"),
            discrepancy=Decimal("11000.00"),
        )
    )
    InvestigationFindingRepository(db_connection).create(
        case.investigation_id,
        InvestigationFinding(
            root_causes=["CASH_MOVEMENT_MISMATCH"],
            impact=Decimal("11000.00"),
            severity="HIGH",
            evidence=["No completed cash movement was recorded"],
            recommended_action="Review the settlement instruction.",
        ),
    )
    return case


def test_submitter_cannot_self_approve_and_reviewer_can_approve(
    db_connection,
    test_settlement,
    approval_api,
):
    client, set_user = approval_api
    case = create_reviewable_case(db_connection, test_settlement)
    explanation_run_id = uuid4()
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO ai.explanation_runs (
                run_id,
                investigation_id,
                requested_by_user_id,
                provider,
                model,
                prompt_version,
                status,
                input_snapshot,
                input_sha256,
                output_snapshot,
                started_at,
                duration_ms
            )
            VALUES (
                %s, %s, 1, 'deterministic-demo-provider',
                'deterministic-v1', 'test-v1', 'SUCCEEDED',
                '{}'::jsonb, %s, '{}'::jsonb, CURRENT_TIMESTAMP, 1
            )
            """,
            (explanation_run_id, case.investigation_id, "a" * 64),
        )
    set_user(1, "ANALYST")

    submission = client.post(
        f"/investigations/{case.investigation_id}/submit-for-approval",
        json={
            "comment": "Please review the finding and proposed action.",
            "explanation_run_id": str(explanation_run_id),
        },
    )

    assert submission.status_code == 200
    assert submission.json()["event_type"] == "SUBMITTED_FOR_APPROVAL"
    assert submission.json()["new_status"] == "PENDING_APPROVAL"

    set_user(1, "REVIEWER")
    self_approval = client.post(
        f"/investigations/{case.investigation_id}/decision",
        json={"decision": "APPROVE", "comment": "Reviewed and approved."},
    )
    assert self_approval.status_code == 409

    set_user(2, "REVIEWER")
    approval = client.post(
        f"/investigations/{case.investigation_id}/decision",
        json={"decision": "APPROVE", "comment": "Evidence checked and approved."},
    )
    assert approval.status_code == 200
    assert approval.json()["event_type"] == "APPROVED"
    assert approval.json()["new_status"] == "APPROVED"

    direct_update = client.put(
        f"/investigations/{case.investigation_id}/",
        params={"status": "CLOSED"},
    )
    assert direct_update.status_code == 409

    with db_connection.cursor() as cursor:
        cursor.execute(
            "SELECT status FROM investigation.cases WHERE investigation_id = %s",
            (case.investigation_id,),
        )
        case_status = cursor.fetchone()[0]
        cursor.execute(
            """
            SELECT event_type, actor_user_id, previous_status, new_status
            FROM investigation.approval_events
            WHERE investigation_id = %s
            ORDER BY approval_event_id
            """,
            (case.investigation_id,),
        )
        events = cursor.fetchall()

    assert case_status == "APPROVED"
    assert events == [
        ("SUBMITTED_FOR_APPROVAL", 1, "OPEN", "PENDING_APPROVAL"),
        ("APPROVED", 2, "PENDING_APPROVAL", "APPROVED"),
    ]
    set_user(1, "ANALYST")
    history = client.get(
        f"/investigations/{case.investigation_id}/approval-events"
    )
    assert history.status_code == 200
    assert len(history.json()) == 2
    assert history.json()[0]["explanation_run_id"] == str(explanation_run_id)
    assert UUID(history.json()[1]["explanation_run_id"]) == explanation_run_id


def test_reviewer_can_request_changes(
    db_connection,
    test_settlement,
    approval_api,
):
    client, set_user = approval_api
    case = create_reviewable_case(db_connection, test_settlement)
    set_user(1, "ANALYST")

    submission = client.post(
        f"/investigations/{case.investigation_id}/submit-for-approval",
        json={"comment": "Please review this investigation."},
    )
    assert submission.status_code == 200

    set_user(2, "REVIEWER")
    decision = client.post(
        f"/investigations/{case.investigation_id}/decision",
        json={
            "decision": "REQUEST_CHANGES",
            "comment": "Attach the settlement instruction evidence.",
        },
    )

    assert decision.status_code == 200
    assert decision.json()["event_type"] == "CHANGES_REQUESTED"
    assert decision.json()["new_status"] == "INVESTIGATING"

    set_user(1, "ANALYST")
    resubmission = client.post(
        f"/investigations/{case.investigation_id}/submit-for-approval",
        json={"comment": "Updated the evidence and resubmitting."},
    )
    assert resubmission.status_code == 200
    assert resubmission.json()["previous_status"] == "INVESTIGATING"

    set_user(2, "REVIEWER")
    rejection = client.post(
        f"/investigations/{case.investigation_id}/decision",
        json={"decision": "REJECT", "comment": "Evidence remains insufficient."},
    )
    assert rejection.status_code == 200
    assert rejection.json()["event_type"] == "REJECTED"
    assert rejection.json()["new_status"] == "REJECTED"
    history = client.get(
        f"/investigations/{case.investigation_id}/approval-events"
    )
    assert history.status_code == 200
    assert [event["event_type"] for event in history.json()] == [
        "SUBMITTED_FOR_APPROVAL",
        "CHANGES_REQUESTED",
        "SUBMITTED_FOR_APPROVAL",
        "REJECTED",
    ]
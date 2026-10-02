from decimal import Decimal

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


def create_test_case(db_connection, settlement_id):
    case = InvestigationCase(
        investigation_id=None,
        settlement_id=settlement_id,
        expected_cash=Decimal("11000.00"),
        actual_cash=Decimal("0.00"),
        discrepancy=Decimal("11000.00"),
    )

    return InvestigationCaseRepository(db_connection).create(case)


def test_create_investigation_finding(
    db_connection,
    test_settlement,
):
    saved_case = create_test_case(
        db_connection,
        test_settlement,
    )

    finding = InvestigationFinding(
        root_causes=[
            "INVALID_SETTLEMENT_INSTRUCTION",
            "CASH_MOVEMENT_MISMATCH",
        ],
        impact=Decimal("11000.00"),
        severity="HIGH",
        evidence=["No completed cash movement was recorded"],
        recommended_action=None,
    )

    repository = InvestigationFindingRepository(db_connection)
    finding_id = repository.create(saved_case.investigation_id, finding)

    assert finding_id is not None

    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                investigation_id,
                root_causes,
                impact,
                severity,
                recommended_action
            FROM investigation.findings
            WHERE finding_id = %s
            """,
            (finding_id,),
        )
        row = cursor.fetchone()

    assert row == (
        saved_case.investigation_id,
        [
            "INVALID_SETTLEMENT_INSTRUCTION",
            "CASH_MOVEMENT_MISMATCH",
        ],
        Decimal("11000.00"),
        "HIGH",
        None,
    )


def test_create_investigation_evidence(
    db_connection,
    test_settlement,
):
    saved_case = create_test_case(
        db_connection,
        test_settlement,
    )

    repository = InvestigationEvidenceRepository(db_connection)
    evidence_id = repository.create(
        investigation_id=saved_case.investigation_id,
        evidence_type="FINANCIAL_RECORD",
        source_table="financial.settlements",
        source_record_id=test_settlement,
        evidence_text="Settlement failed with INVALID_SETTLEMENT_INSTRUCTION",
    )

    assert evidence_id is not None

    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                investigation_id,
                evidence_type,
                source_table,
                source_record_id,
                evidence_text
            FROM investigation.evidence
            WHERE evidence_id = %s
            """,
            (evidence_id,),
        )
        row = cursor.fetchone()

    assert row == (
        saved_case.investigation_id,
        "FINANCIAL_RECORD",
        "financial.settlements",
        test_settlement,
        "Settlement failed with INVALID_SETTLEMENT_INSTRUCTION",
    )

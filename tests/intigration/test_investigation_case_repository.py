from decimal import Decimal

from app.database.repositories.investigation_case_repository import (
    InvestigationCaseRepository,
)
from app.investigation.models import InvestigationCase


def test_create_investigation_case(
    db_connection,
    test_settlement,
):
    case = InvestigationCase(
        investigation_id=None,
        settlement_id=test_settlement,
        expected_cash=Decimal("11000.00"),
        actual_cash=Decimal("0.00"),
        discrepancy=Decimal("11000.00"),
    )

    repository = InvestigationCaseRepository(
        db_connection
    )

    saved_case = repository.create(case)

    assert saved_case.investigation_id is not None
    assert saved_case.settlement_id == test_settlement
    assert saved_case.expected_cash == Decimal("11000.00")
    assert saved_case.actual_cash == Decimal("0.00")
    assert saved_case.discrepancy == Decimal("11000.00")
from decimal import Decimal
import pytest

from app.database.repositories.transaction_repository import (
    TransactionRepository
)

from app.investigation.models import TransactionEvidence


def test_get_investigation_data(
    db_connection,
    test_transaction
):

    repository = TransactionRepository(
        db_connection
    )

    result = repository.get_investigation_data(
        test_transaction
    )

    assert isinstance(
        result,
        TransactionEvidence
    )

    assert result.transaction_id == test_transaction

    assert result.transaction_type == "SELL"

    assert result.gross_amount == Decimal("15000.00")

    assert result.fee_amount == Decimal("0.00")

    assert result.net_amount == Decimal("15000.00")

    assert result.status == "COMPLETED"


def test_get_investigation_data_raises_when_transaction_missing(
    db_connection
):

    repository = TransactionRepository(
        db_connection
    )

    with pytest.raises(
        ValueError,
        match="Transaction not found"
    ):
        repository.get_investigation_data(999999)
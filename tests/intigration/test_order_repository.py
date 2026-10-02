from datetime import datetime
import pytest

from app.database.repositories.order_repository import (
    OrderRepository
)

from app.investigation.models import OrderEvidence


def test_get_investigation_data(
    db_connection,
    test_order,
    test_account
):

    repository = OrderRepository(
        db_connection
    )

    result = repository.get_investigation_data(
        test_order
    )

    assert isinstance(
        result,
        OrderEvidence
    )

    assert result.order_id == test_order

    assert result.account_id == test_account

    assert result.security_id == 1

    assert result.side == "SELL"

    assert result.order_type == "MARKET"

    assert result.quantity == 20

    assert result.limit_price is None

    assert result.status == "COMPLETED"

    assert isinstance(
        result.created_at,
        datetime
    )

def test_get_investigation_data_raises_when_order_missing(
    db_connection
):

    repository = OrderRepository(
        db_connection
    )

    with pytest.raises(
        ValueError,
        match="Order not found"
    ):
        repository.get_investigation_data(999999)
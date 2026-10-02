from datetime import datetime, timezone
from decimal import Decimal

from app.database.repositories.execution_repository import (
    ExecutionRepository
)

from app.investigation.models import ExecutionEvidence


def test_get_investigation_data(
    db_connection,
    test_order
):

    execution_time = datetime.now(timezone.utc)

    with db_connection.cursor() as cursor:

        cursor.execute(
            """
            INSERT INTO financial.executions (
                order_id,
                execution_quantity,
                execution_price,
                execution_time,
                status
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s
            )
            RETURNING execution_id;
            """,
            (
                test_order,
                20,
                Decimal("550.00"),
                execution_time,
                "COMPLETED"
            )
        )

        execution_id = cursor.fetchone()[0]

    repository = ExecutionRepository(
        db_connection
    )

    result = repository.get_investigation_data(
        test_order
    )

    assert len(result) == 1

    evidence = result[0]

    assert isinstance(
        evidence,
        ExecutionEvidence
    )

    assert evidence.execution_id == execution_id

    assert evidence.order_id == test_order

    assert evidence.execution_quantity == 20

    assert evidence.execution_price == Decimal("550.00")

    assert evidence.execution_time == execution_time

    assert evidence.status == "COMPLETED"

def test_get_multiple_executions(
    db_connection,
    test_order
):

    with db_connection.cursor() as cursor:

        cursor.execute(
            """
            INSERT INTO financial.executions (
                order_id,
                execution_quantity,
                execution_price,
                execution_time,
                status
            )
            VALUES
                (
                    %s,
                    10,
                    550.00,
                    '2026-08-31 10:00:00+00',
                    'COMPLETED'
                ),
                (
                    %s,
                    10,
                    551.00,
                    '2026-08-31 10:01:00+00',
                    'COMPLETED'
                );
            """,
            (
                test_order,
                test_order
            )
        )

    repository = ExecutionRepository(
        db_connection
    )

    result = repository.get_investigation_data(
        test_order
    )

    assert len(result) == 2

    assert result[0].execution_quantity == 10
    assert result[0].execution_price == Decimal("550.00")

    assert result[1].execution_quantity == 10
    assert result[1].execution_price == Decimal("551.00")

    assert (
        result[0].execution_time
        < result[1].execution_time
    )


def test_get_multiple_executions(
    db_connection,
    test_order
):

    with db_connection.cursor() as cursor:

        cursor.execute(
            """
            INSERT INTO financial.executions (
                order_id,
                execution_quantity,
                execution_price,
                execution_time,
                status
            )
            VALUES
                (
                    %s,
                    10,
                    550.00,
                    '2026-08-31 10:00:00+00',
                    'COMPLETED'
                ),
                (
                    %s,
                    10,
                    551.00,
                    '2026-08-31 10:01:00+00',
                    'COMPLETED'
                );
            """,
            (
                test_order,
                test_order
            )
        )

    repository = ExecutionRepository(
        db_connection
    )

    result = repository.get_investigation_data(
        test_order
    )

    assert len(result) == 2

    assert result[0].execution_quantity == 10
    assert result[0].execution_price == Decimal("550.00")

    assert result[1].execution_quantity == 10
    assert result[1].execution_price == Decimal("551.00")

    assert (
        result[0].execution_time
        < result[1].execution_time
    )
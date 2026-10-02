import pytest
from uuid import uuid4

from app.database.connection import get_connection


@pytest.fixture
def db_connection():

    connection = get_connection()

    try:
        connection.autocommit = False
        yield connection

    finally:
        connection.rollback()
        connection.close()

@pytest.fixture
def test_transaction(db_connection, test_order):
    with db_connection.cursor() as cursor:
        cursor.execute("""
        INSERT INTO financial.transactions (
                transaction_type,
                gross_amount,
                fee_amount,
                net_amount,
                status,
                order_id
            )
            VALUES (
                'SELL',
                15000.00,
                0.00,
                15000.00,
                'COMPLETED',
                %s
            )
            RETURNING transaction_id;
        """,
        (test_order,)
        )

        transaction_id = cursor.fetchone()[0]
    return transaction_id

@pytest.fixture
def test_customer(db_connection):
    email = f"test.customer.{uuid4()}@example.com"

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
            VALUES (
                'Test',
                'Customer',
                %s,
                '9999999999',
                'ACTIVE'
            )
            RETURNING customer_id;
            """,
            (email,),
        )

        customer_id = cursor.fetchone()[0]

    return customer_id

@pytest.fixture
def test_account(db_connection, test_customer):

    with db_connection.cursor() as cursor:

        cursor.execute(
            """
            INSERT INTO financial.accounts (
                customer_id,
                account_type,
                currency,
                status
            )
            VALUES (
                %s,
                'INVESTMENT',
                'INR',
                'ACTIVE'
            )
            RETURNING account_id;
            """,
            (test_customer,)
        )

        account_id = cursor.fetchone()[0]

    return account_id

@pytest.fixture
def test_settlement(db_connection, test_transaction):

    with db_connection.cursor() as cursor:

        cursor.execute(
            """
            INSERT INTO financial.settlements (
                transaction_id,
                settlement_type,
                expected_cash_amount,
                settled_cash_amount,
                status,
                failure_reason
            )
            VALUES (
                %s,
                'CASH_RECEIVABLE',
                11000.00,
                0.00,
                'FAILED',
                'INVALID_SETTLEMENT_INSTRUCTION'
            )
            RETURNING settlement_id;
            """,
            (test_transaction,)
        )

        settlement_id = cursor.fetchone()[0]

    return settlement_id

@pytest.fixture
def test_cash_movement(
    db_connection,
    test_settlement,
    test_account
):

    with db_connection.cursor() as cursor:

        cursor.execute(
            """
            INSERT INTO financial.cash_movements (
                settlement_id,
                account_id,
                movement_type,
                direction,
                amount,
                currency,
                status,
                movement_date
            )
            VALUES (
                %s,
                %s,
                'SETTLEMENT',
                'CREDIT',
                11000.00,
                'INR',
                'COMPLETED',
                CURRENT_TIMESTAMP
            )
            RETURNING cash_movement_id;
            """,
            (
                test_settlement,
                test_account
            )
        )

        cash_movement_id = cursor.fetchone()[0]

    return cash_movement_id

"""test_cash_movement
      │
      ├──────────────┐
      ▼              ▼
test_settlement   test_account
      │              │
      ▼              ▼
test_transaction test_customer
      │              │
      └──────┬───────┘
             ▼
        db_connection
        """

@pytest.fixture
def test_order(
    db_connection,
    test_account,
):
    with db_connection.cursor() as cursor:

        cursor.execute(
            """
            INSERT INTO financial.orders (
                account_id,
                security_id,
                side,
                order_type,
                quantity,
                limit_price,
                status
            )
            VALUES (
                %s,
                1,
                'SELL',
                'MARKET',
                20,
                NULL,
                'COMPLETED'
            )
            RETURNING order_id;
            """,
            (test_account,)
        )

        order_id = cursor.fetchone()[0]

    return order_id
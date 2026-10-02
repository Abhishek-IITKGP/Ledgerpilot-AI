from app.investigation.models import OrderEvidence


class OrderRepository:

    def __init__(self, connection):
        self.connection = connection

    def get_investigation_data(
        self,
        order_id: int
    ) -> OrderEvidence:

        query = """
            SELECT
                order_id,
                account_id,
                security_id,
                side,
                order_type,
                quantity,
                limit_price,
                status,
                created_at
            FROM financial.orders
            WHERE order_id = %s
        """

        with self.connection.cursor() as cursor:

            cursor.execute(
                query,
                (order_id,)
            )

            row = cursor.fetchone()

        if row is None:
            raise ValueError(
                f"Order not found: {order_id}"
            )

        return OrderEvidence(
            order_id=row[0],
            account_id=row[1],
            security_id=row[2],
            side=row[3],
            order_type=row[4],
            quantity=row[5],
            limit_price=row[6],
            status=row[7],
            created_at=row[8]
        )
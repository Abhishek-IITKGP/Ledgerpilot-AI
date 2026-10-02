from app.investigation.models import TransactionEvidence


class TransactionRepository:

    def __init__(self, connection):
        self.connection = connection

    def get_investigation_data(
        self,
        transaction_id: int
    ) -> TransactionEvidence:

        query = """
            SELECT
                transaction_id,
                transaction_type,
                gross_amount,
                fee_amount,
                net_amount,
                status,
                order_id
            FROM financial.transactions
            WHERE transaction_id = %s
        """

        with self.connection.cursor() as cursor:

            cursor.execute(
                query,
                (transaction_id,)
            )

            row = cursor.fetchone()

        if row is None:
            raise ValueError(
                f"Transaction not found: {transaction_id}"
            )

        return TransactionEvidence(
            transaction_id=row[0],
            transaction_type=row[1],
            gross_amount=row[2],
            fee_amount=row[3],
            net_amount=row[4],
            status=row[5],
            order_id=row[6]
        )
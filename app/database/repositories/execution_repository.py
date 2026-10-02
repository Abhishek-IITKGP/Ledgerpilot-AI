from app.investigation.models import ExecutionEvidence


class ExecutionRepository:

    def __init__(self, connection):
        self.connection = connection

    def get_investigation_data(
        self,
        order_id: int
    ) -> list[ExecutionEvidence]:

        query = """
            SELECT
                execution_id,
                order_id,
                execution_quantity,
                execution_price,
                execution_time,
                status
            FROM financial.executions
            WHERE order_id = %s
            ORDER BY execution_time;
        """

        with self.connection.cursor() as cursor:

            cursor.execute(
                query,
                (order_id,)
            )

            rows = cursor.fetchall()

        return [
            ExecutionEvidence(
                execution_id=row[0],
                order_id=row[1],
                execution_quantity=row[2],
                execution_price=row[3],
                execution_time=row[4],
                status=row[5]
            )
            for row in rows
        ]
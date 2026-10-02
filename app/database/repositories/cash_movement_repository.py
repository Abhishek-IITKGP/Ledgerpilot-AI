from decimal import Decimal

from app.financial.models import CashMovementData, CashMovementStatus, CashMovementDirection


class CashMovementRepository:

    def __init__(self, connection):
        self.connection = connection

    def get_by_settlement(
        self,
        settlement_id: int
    ) -> list[CashMovementData]:

        query = """
            SELECT
                cash_movement_id,
                settlement_id,
                account_id,
                movement_type,
                direction,
                amount,
                currency,
                status
            FROM financial.cash_movements
            WHERE settlement_id = %s
            ORDER BY cash_movement_id
        """

        with self.connection.cursor() as cursor:

            cursor.execute(
                query,
                (settlement_id,)
            )

            rows = cursor.fetchall()

        return [
            CashMovementData(
                cash_movement_id=row[0],
                settlement_id=row[1],
                account_id=row[2],
                movement_type=row[3],
                direction=CashMovementDirection(row[4]),
                amount=Decimal(row[5]),
                currency=row[6],
                status=CashMovementStatus(row[7])
            )
            for row in rows
        ]
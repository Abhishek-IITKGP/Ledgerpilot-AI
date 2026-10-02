from decimal import Decimal

from app.financial.models import SettlementCashData
from app.investigation.models import SettlementEvidence


class SettlementRepository:

    def __init__(self, connection):
        self.connection = connection

    def get_cash_data(
        self,
        settlement_id: int
    ) -> SettlementCashData:

        query = """
            SELECT
                settlement_id,
                expected_cash_amount,
                settled_cash_amount
            FROM financial.settlements
            WHERE settlement_id = %s
        """

        with self.connection.cursor() as cursor:

            cursor.execute(
                query,
                (settlement_id,)
            )

            row = cursor.fetchone()

        if row is None:
            raise ValueError(
                f"Settlement {settlement_id} not found"
            )

        return SettlementCashData(
            settlement_id=row[0],
            expected_cash=Decimal(row[1]),
            actual_cash=Decimal(row[2])
        )

    def get_investigation_data(
    self,
    settlement_id: int
    ) -> SettlementEvidence:

        query = """
            SELECT
                settlement_id,
                transaction_id,
                settlement_type,
                expected_cash_amount,
                settled_cash_amount,
                status,
                failure_reason
            FROM financial.settlements
            WHERE settlement_id = %s
        """

        with self.connection.cursor() as cursor:

            cursor.execute(
                query,
                (settlement_id,)
            )

            row = cursor.fetchone()

        if row is None:
            raise ValueError(
                f"Settlement not found: {settlement_id}"
            )

        return SettlementEvidence(
            settlement_id=row[0],
            transaction_id=row[1],
            settlement_type=row[2],
            expected_cash=row[3],
            settled_cash=row[4],
            status=row[5],
            failure_reason=row[6]
        )
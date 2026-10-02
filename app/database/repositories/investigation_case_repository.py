from decimal import Decimal

from app.investigation.models import InvestigationCase


class InvestigationCaseRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(
        self,
        case: InvestigationCase,
    ) -> InvestigationCase:
        query = """
            INSERT INTO investigation.cases (
                settlement_id,
                expected_cash,
                actual_cash,
                discrepancy,
                status,
                investigation_type,
                idempotency_key
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING
                investigation_id,
                settlement_id,
                expected_cash,
                actual_cash,
                discrepancy,
                investigation_type,
                idempotency_key
        """

        with self.connection.cursor() as cursor:
            cursor.execute(
                query,
                (
                    case.settlement_id,
                    case.expected_cash,
                    case.actual_cash,
                    case.discrepancy,
                    "OPEN",
                    case.investigation_type,
                    case.idempotency_key,
                ),
            )

            row = cursor.fetchone()

        return InvestigationCase(
            investigation_id=row[0],
            settlement_id=row[1],
            expected_cash=Decimal(row[2]),
            actual_cash=Decimal(row[3]),
            discrepancy=Decimal(row[4]),
            investigation_type=row[5],
            idempotency_key=row[6],
        )

    def get_by_request(
        self,
        settlement_id: int,
        investigation_type: str,
        idempotency_key: str,
    ) -> InvestigationCase | None:
        query = """
            SELECT
                investigation_id,
                settlement_id,
                expected_cash,
                actual_cash,
                discrepancy,
                investigation_type,
                idempotency_key
            FROM investigation.cases
            WHERE settlement_id = %s
              AND investigation_type = %s
              AND idempotency_key = %s
        """

        with self.connection.cursor() as cursor:
            cursor.execute(
                query,
                (settlement_id, investigation_type, idempotency_key),
            )
            row = cursor.fetchone()

        if row is None:
            return None

        return InvestigationCase(
            investigation_id=row[0],
            settlement_id=row[1],
            expected_cash=Decimal(row[2]),
            actual_cash=Decimal(row[3]),
            discrepancy=Decimal(row[4]),
            investigation_type=row[5],
            idempotency_key=row[6],
        )
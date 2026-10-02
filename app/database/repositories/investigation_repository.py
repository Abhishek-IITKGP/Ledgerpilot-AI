from decimal import Decimal

from app.investigation.models import (
    InvestigationCase,
    InvestigationFinding,
    InvestigationRecord
)
from app.financial.models import InvestigationStatus


class InvestigationRepository:
    def __init__(self, connection):
        self.connection = connection

    def get_by_id(
        self,
        investigation_id: int,
    ) -> InvestigationRecord | None:
        case_query = """
            SELECT
                investigation_id,
                settlement_id,
                expected_cash,
                actual_cash,
                discrepancy,
                investigation_type,
                idempotency_key,
                status,
                created_at,
                updated_at
            FROM investigation.cases
            WHERE investigation_id = %s
        """

        finding_query = """
            SELECT
                root_causes,
                impact,
                severity,
                recommended_action
            FROM investigation.findings
            WHERE investigation_id = %s
            ORDER BY finding_id DESC
            LIMIT 1
        """

        evidence_query = """
            SELECT evidence_text
            FROM investigation.evidence
            WHERE investigation_id = %s
            ORDER BY evidence_id
        """

        with self.connection.cursor() as cursor:
            cursor.execute(case_query, (investigation_id,))
            case_row = cursor.fetchone()

            if case_row is None:
                return None

            cursor.execute(
                finding_query,
                (investigation_id,),
            )
            finding_row = cursor.fetchone()

            cursor.execute(
                evidence_query,
                (investigation_id,),
            )
            evidence_rows = cursor.fetchall()

        case = InvestigationCase(
            investigation_id=case_row[0],
            settlement_id=case_row[1],
            expected_cash=Decimal(case_row[2]),
            actual_cash=Decimal(case_row[3]),
            discrepancy=Decimal(case_row[4]),
            investigation_type=case_row[5],
            idempotency_key=case_row[6],
        )

        finding = None

        if finding_row is not None:
            finding = InvestigationFinding(
                root_causes=finding_row[0],
                impact=Decimal(finding_row[1]),
                severity=finding_row[2],
                evidence=[
                    row[0]
                    for row in evidence_rows
                ],
                recommended_action=finding_row[3],
            )

        return InvestigationRecord(
            case=case,
            status=case_row[7],
            created_at=case_row[8],
            updated_at=case_row[9],
            finding=finding,
        )

    def get_by_request(
        self,
        settlement_id: int,
        investigation_type: str,
        idempotency_key: str,
    ) -> InvestigationRecord | None:
        query = """
            SELECT investigation_id
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

        return self.get_by_id(row[0])

    def list_investigations(
    self,
    settlement_id: int | None = None,
    status: str | None = None,
    severity: str | None = None,
    investigation_type: str | None = None,
    ) -> list[tuple]:
        query = """
            SELECT
                c.investigation_id,
                c.settlement_id,
                c.investigation_type,
                c.status,
                c.discrepancy,
                f.severity,
                c.created_at
            FROM investigation.cases AS c
            LEFT JOIN LATERAL (
                SELECT finding.severity
                FROM investigation.findings AS finding
                WHERE finding.investigation_id = c.investigation_id
                ORDER BY finding.finding_id DESC
                LIMIT 1
            ) AS f ON TRUE
            WHERE 1 = 1
        """

        parameters = []

        if settlement_id is not None:
            query += " AND c.settlement_id = %s"
            parameters.append(settlement_id)

        if status is not None:
            query += " AND c.status = %s"
            parameters.append(status)

        if severity is not None:
            query += " AND f.severity = %s"
            parameters.append(severity)

        if investigation_type is not None:
            query += " AND c.investigation_type = %s"
            parameters.append(investigation_type)

        query += " ORDER BY c.created_at DESC"

        with self.connection.cursor() as cursor:
            cursor.execute(query, parameters)
            return cursor.fetchall()


    def update_investigation_status(
        self,
        investigation_id: int,
        status: InvestigationStatus,
    ) -> InvestigationRecord | None:
        query = """
            UPDATE investigation.cases
            SET status = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE investigation_id = %s
        """

        with self.connection.cursor() as cursor:
            cursor.execute(
                query,
                (status.value, investigation_id),
            )

            if cursor.rowcount == 0:
                return None

        return self.get_by_id(investigation_id)
        

from app.investigation.models import InvestigationFinding


class InvestigationFindingRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(
        self,
        investigation_id: int,
        finding: InvestigationFinding,
    ) -> int:
        query = """
            INSERT INTO investigation.findings (
                investigation_id,
                root_causes,
                impact,
                severity,
                recommended_action
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING finding_id
        """

        with self.connection.cursor() as cursor:
            cursor.execute(
                query,
                (
                    investigation_id,
                    finding.root_causes,
                    finding.impact,
                    finding.severity,
                    finding.recommended_action,
                ),
            )

            row = cursor.fetchone()

        return row[0]

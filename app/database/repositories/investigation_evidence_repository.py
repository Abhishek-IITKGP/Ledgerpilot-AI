class InvestigationEvidenceRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(
        self,
        investigation_id: int,
        evidence_type: str,
        evidence_text: str,
        source_table: str | None = None,
        source_record_id: int | None = None,
    ) -> int:
        query = """
            INSERT INTO investigation.evidence (
                investigation_id,
                evidence_type,
                source_table,
                source_record_id,
                evidence_text
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING evidence_id
        """

        with self.connection.cursor() as cursor:
            cursor.execute(
                query,
                (
                    investigation_id,
                    evidence_type,
                    source_table,
                    source_record_id,
                    evidence_text,
                ),
            )

            row = cursor.fetchone()

        return row[0]

from app.ai.models import RetrievedPolicyChunk


class PolicyRepository:
    def __init__(self, connection):
        self.connection = connection

    def search_approved_chunks(
        self,
        search_terms: list[str],
        limit: int = 5,
    ) -> list[RetrievedPolicyChunk]:
        normalized_terms = sorted(
            {term.strip().lower() for term in search_terms if term.strip()}
        )
        if not normalized_terms:
            return []

        query_text = " ".join(normalized_terms)
        query = """
            SELECT
                d.document_key,
                d.title,
                d.source_name,
                d.version,
                c.chunk_index,
                c.content
            FROM ai.policy_chunks AS c
            JOIN ai.policy_documents AS d
                ON d.document_id = c.document_id
            WHERE d.publication_status = 'APPROVED'
              AND d.is_active = TRUE
              AND CURRENT_DATE >= d.effective_from
              AND (d.effective_to IS NULL OR CURRENT_DATE <= d.effective_to)
              AND (
                  c.keywords && %s::text[]
                  OR c.search_vector @@ plainto_tsquery('english', %s)
              )
            ORDER BY
                (c.keywords && %s::text[]) DESC,
                ts_rank_cd(
                    c.search_vector,
                    plainto_tsquery('english', %s)
                ) DESC,
                d.document_key,
                c.chunk_index
            LIMIT %s
        """

        with self.connection.cursor() as cursor:
            cursor.execute(
                query,
                (
                    normalized_terms,
                    query_text,
                    normalized_terms,
                    query_text,
                    limit,
                ),
            )
            rows = cursor.fetchall()

        return [
            RetrievedPolicyChunk(
                reference=f"{row[0]}@{row[3]}#chunk-{row[4]}",
                title=row[1],
                source_name=row[2],
                content=row[5],
            )
            for row in rows
        ]
import json
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4


class AIExplanationAuditRepository:
    def __init__(self, connection):
        self.connection = connection

    def record_run(
        self,
        *,
        investigation_id: int,
        requested_by_user_id: int,
        provider: str,
        model: str,
        prompt_version: str,
        status: str,
        input_snapshot: dict[str, Any],
        input_sha256: str,
        started_at: datetime,
        duration_ms: int,
        output_snapshot: dict[str, Any] | None = None,
        error_category: str | None = None,
    ) -> UUID:
        run_id = uuid4()
        query = """
            INSERT INTO ai.explanation_runs (
                run_id,
                investigation_id,
                requested_by_user_id,
                provider,
                model,
                prompt_version,
                status,
                input_snapshot,
                input_sha256,
                output_snapshot,
                error_category,
                started_at,
                duration_ms
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                %s::jsonb, %s, %s::jsonb, %s, %s, %s
            )
            RETURNING run_id
        """

        with self.connection.cursor() as cursor:
            cursor.execute(
                query,
                (
                    run_id,
                    investigation_id,
                    requested_by_user_id,
                    provider,
                    model,
                    prompt_version,
                    status,
                    json.dumps(input_snapshot, sort_keys=True),
                    input_sha256,
                    (
                        json.dumps(output_snapshot, sort_keys=True)
                        if output_snapshot is not None
                        else None
                    ),
                    error_category,
                    started_at,
                    duration_ms,
                ),
            )
            saved_run_id = cursor.fetchone()[0]

        self.connection.commit()
        return saved_run_id

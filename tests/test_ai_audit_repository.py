from datetime import datetime, timezone
from uuid import UUID

from app.database.repositories.ai_explanation_audit_repository import (
    AIExplanationAuditRepository,
)


class FakeCursor:
    def __init__(self):
        self.query = None
        self.parameters = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, query, parameters):
        self.query = query
        self.parameters = parameters

    def fetchone(self):
        return (self.parameters[0],)


class FakeConnection:
    def __init__(self):
        self.fake_cursor = FakeCursor()
        self.committed = False

    def cursor(self):
        return self.fake_cursor

    def commit(self):
        self.committed = True


def test_record_run_inserts_audit_snapshot_and_commits():
    connection = FakeConnection()
    repository = AIExplanationAuditRepository(connection)
    started_at = datetime.now(timezone.utc)

    run_id = repository.record_run(
        investigation_id=42,
        requested_by_user_id=3,
        provider="deterministic-demo-provider",
        model="deterministic-v1",
        prompt_version="investigation-explanation-v1",
        status="SUCCEEDED",
        input_snapshot={"finding": {"discrepancy": "11000.00"}},
        input_sha256="a" * 64,
        started_at=started_at,
        duration_ms=12,
        output_snapshot={"summary": "Evidence-based explanation"},
    )

    assert isinstance(run_id, UUID)
    assert "INSERT INTO ai.explanation_runs" in connection.fake_cursor.query
    assert connection.fake_cursor.parameters[1:7] == (
        42,
        3,
        "deterministic-demo-provider",
        "deterministic-v1",
        "investigation-explanation-v1",
        "SUCCEEDED",
    )
    assert connection.fake_cursor.parameters[7] == (
        '{"finding": {"discrepancy": "11000.00"}}'
    )
    assert connection.fake_cursor.parameters[9] == (
        '{"summary": "Evidence-based explanation"}'
    )
    assert connection.committed is True

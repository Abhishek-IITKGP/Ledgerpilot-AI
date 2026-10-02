BEGIN;

CREATE SCHEMA IF NOT EXISTS ai;

CREATE TABLE IF NOT EXISTS ai.explanation_runs (
    run_id UUID PRIMARY KEY,
    investigation_id BIGINT NOT NULL
        REFERENCES investigation.cases(investigation_id),
    requested_by_user_id INTEGER NOT NULL
        REFERENCES authentication.users(userid),
    provider VARCHAR(100) NOT NULL,
    model VARCHAR(200) NOT NULL,
    prompt_version VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    input_snapshot JSONB NOT NULL,
    input_sha256 CHAR(64) NOT NULL,
    output_snapshot JSONB,
    error_category VARCHAR(50),
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    duration_ms BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT explanation_runs_status_check
        CHECK (status IN ('SUCCEEDED', 'FAILED')),
    CONSTRAINT explanation_runs_outcome_check
        CHECK (
            (status = 'SUCCEEDED' AND output_snapshot IS NOT NULL
                AND error_category IS NULL)
            OR
            (status = 'FAILED' AND output_snapshot IS NULL
                AND error_category IS NOT NULL)
        ),
    CONSTRAINT explanation_runs_duration_check
        CHECK (duration_ms >= 0)
);

CREATE INDEX IF NOT EXISTS idx_explanation_runs_investigation
    ON ai.explanation_runs (investigation_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_explanation_runs_actor
    ON ai.explanation_runs (requested_by_user_id, created_at DESC);

CREATE OR REPLACE FUNCTION ai.reject_explanation_run_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'AI explanation audit records are immutable';
END;
$$;

DROP TRIGGER IF EXISTS explanation_runs_no_update_delete
    ON ai.explanation_runs;
CREATE TRIGGER explanation_runs_no_update_delete
    BEFORE UPDATE OR DELETE ON ai.explanation_runs
    FOR EACH ROW
    EXECUTE FUNCTION ai.reject_explanation_run_mutation();

DROP TRIGGER IF EXISTS explanation_runs_no_truncate
    ON ai.explanation_runs;
CREATE TRIGGER explanation_runs_no_truncate
    BEFORE TRUNCATE ON ai.explanation_runs
    FOR EACH STATEMENT
    EXECUTE FUNCTION ai.reject_explanation_run_mutation();

COMMIT;

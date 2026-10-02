BEGIN;

CREATE TABLE IF NOT EXISTS investigation.approval_events (
    approval_event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    investigation_id BIGINT NOT NULL
        REFERENCES investigation.cases(investigation_id),
    actor_user_id INTEGER NOT NULL
        REFERENCES authentication.users(userid),
    explanation_run_id UUID
        REFERENCES ai.explanation_runs(run_id),
    event_type VARCHAR(32) NOT NULL,
    previous_status VARCHAR(30) NOT NULL,
    new_status VARCHAR(30) NOT NULL,
    comment TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT approval_events_event_type_check
        CHECK (
            event_type IN (
                'SUBMITTED_FOR_APPROVAL',
                'APPROVED',
                'REJECTED',
                'CHANGES_REQUESTED'
            )
        ),
    CONSTRAINT approval_events_transition_check
        CHECK (
            (event_type = 'SUBMITTED_FOR_APPROVAL'
                AND previous_status IN ('OPEN', 'INVESTIGATING')
                AND new_status = 'PENDING_APPROVAL')
            OR (event_type = 'APPROVED'
                AND previous_status = 'PENDING_APPROVAL'
                AND new_status = 'APPROVED')
            OR (event_type = 'REJECTED'
                AND previous_status = 'PENDING_APPROVAL'
                AND new_status = 'REJECTED')
            OR (event_type = 'CHANGES_REQUESTED'
                AND previous_status = 'PENDING_APPROVAL'
                AND new_status = 'INVESTIGATING')
        ),
    CONSTRAINT approval_events_comment_check
        CHECK (length(btrim(comment)) > 0)
);

CREATE INDEX IF NOT EXISTS idx_approval_events_case_created
    ON investigation.approval_events (
        investigation_id,
        created_at DESC,
        approval_event_id DESC
    );

CREATE OR REPLACE FUNCTION investigation.reject_approval_event_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'Investigation approval events are immutable';
END;
$$;

DROP TRIGGER IF EXISTS approval_events_no_update_delete
    ON investigation.approval_events;
CREATE TRIGGER approval_events_no_update_delete
    BEFORE UPDATE OR DELETE ON investigation.approval_events
    FOR EACH ROW
    EXECUTE FUNCTION investigation.reject_approval_event_mutation();

DROP TRIGGER IF EXISTS approval_events_no_truncate
    ON investigation.approval_events;
CREATE TRIGGER approval_events_no_truncate
    BEFORE TRUNCATE ON investigation.approval_events
    FOR EACH STATEMENT
    EXECUTE FUNCTION investigation.reject_approval_event_mutation();

COMMIT;
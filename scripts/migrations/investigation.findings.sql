BEGIN;

CREATE TABLE IF NOT EXISTS investigation.findings (
    finding_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    investigation_id BIGINT NOT NULL
        REFERENCES investigation.cases(investigation_id),
    root_causes TEXT[] NOT NULL,
    impact NUMERIC(18, 2) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    recommended_action TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT findings_severity_check
        CHECK (
            severity IN (
                'LOW',
                'MEDIUM',
                'HIGH',
                'CRITICAL'
            )
        )
);

COMMIT;
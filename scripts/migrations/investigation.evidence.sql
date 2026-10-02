BEGIN;
CREATE TABLE IF NOT EXISTS investigation.evidence (
    evidence_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    investigation_id BIGINT NOT NULL
        REFERENCES investigation.cases(investigation_id),
    evidence_type VARCHAR(50) NOT NULL,
    source_table VARCHAR(100),
    source_record_id BIGINT,
    evidence_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_findings_investigation_id
    ON investigation.findings (investigation_id);

CREATE INDEX IF NOT EXISTS idx_evidence_investigation_id
    ON investigation.evidence (investigation_id);

COMMIT;
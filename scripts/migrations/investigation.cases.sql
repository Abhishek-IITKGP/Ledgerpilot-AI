BEGIN;

CREATE TABLE IF NOT EXISTS investigation.cases (
    investigation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    settlement_id BIGINT NOT NULL
        REFERENCES financial.settlements(settlement_id),
    expected_cash NUMERIC(18, 2) NOT NULL,
    actual_cash NUMERIC(18, 2) NOT NULL,
    discrepancy NUMERIC(18, 2) NOT NULL,
    investigation_type VARCHAR(50) NOT NULL DEFAULT 'CASH_DISCREPANCY',
    idempotency_key VARCHAR(100),
    status VARCHAR(30) NOT NULL DEFAULT 'OPEN',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT cases_status_check
        CHECK (
            status IN (
                'OPEN',
                'INVESTIGATING',
                'PENDING_APPROVAL',
                'APPROVED',
                'REJECTED',
                'CLOSED'
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_cases_settlement_id
    ON investigation.cases (settlement_id);

ALTER TABLE investigation.cases
    ADD COLUMN IF NOT EXISTS investigation_type VARCHAR(50)
        NOT NULL DEFAULT 'CASH_DISCREPANCY';

ALTER TABLE investigation.cases
    ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(100);

CREATE UNIQUE INDEX IF NOT EXISTS uq_investigation_cases_request
    ON investigation.cases (
        settlement_id,
        investigation_type,
        idempotency_key
    )
    WHERE idempotency_key IS NOT NULL;

COMMIT;
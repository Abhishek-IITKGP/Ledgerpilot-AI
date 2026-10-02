BEGIN;

CREATE SCHEMA IF NOT EXISTS ai;

CREATE TABLE IF NOT EXISTS ai.policy_documents (
    document_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_key VARCHAR(100) NOT NULL,
    title VARCHAR(250) NOT NULL,
    source_name VARCHAR(250) NOT NULL,
    version VARCHAR(50) NOT NULL,
    publication_status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    effective_from DATE NOT NULL DEFAULT CURRENT_DATE,
    effective_to DATE,
    approved_by_user_id INTEGER
        REFERENCES authentication.users(userid),
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT policy_documents_key_version_unique
        UNIQUE (document_key, version),
    CONSTRAINT policy_documents_publication_status_check
        CHECK (publication_status IN ('DRAFT', 'APPROVED', 'RETIRED')),
    CONSTRAINT policy_documents_approval_check
        CHECK (
            publication_status <> 'APPROVED'
            OR (approved_by_user_id IS NOT NULL AND approved_at IS NOT NULL)
        ),
    CONSTRAINT policy_documents_effective_range_check
        CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

CREATE TABLE IF NOT EXISTS ai.policy_chunks (
    chunk_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id BIGINT NOT NULL
        REFERENCES ai.policy_documents(document_id),
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    keywords TEXT[] NOT NULL DEFAULT '{}',
    search_vector TSVECTOR GENERATED ALWAYS AS (
        to_tsvector('english'::regconfig, content)
    ) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT policy_chunks_document_index_unique
        UNIQUE (document_id, chunk_index),
    CONSTRAINT policy_chunks_index_check CHECK (chunk_index >= 0)
);

CREATE INDEX IF NOT EXISTS idx_policy_chunks_search_vector
    ON ai.policy_chunks USING GIN (search_vector);

CREATE INDEX IF NOT EXISTS idx_policy_chunks_keywords
    ON ai.policy_chunks USING GIN (keywords);

CREATE INDEX IF NOT EXISTS idx_policy_documents_approved
    ON ai.policy_documents (effective_from, effective_to)
    WHERE publication_status = 'APPROVED' AND is_active;

COMMIT;
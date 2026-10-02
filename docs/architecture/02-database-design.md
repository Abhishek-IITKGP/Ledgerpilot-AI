# FinSight AI: Database Design and Data Flow

This ERD reflects the tables and declared primary/foreign keys observed in the
configured PostgreSQL database. It includes the full `authentication`,
`financial`, `investigation`, and `ai` application schemas, not only the tables
used by one API request.

```mermaid
erDiagram
    AUTHENTICATION_USERS {
        int userid PK
        varchar username
        varchar email
        text password_hash
        boolean is_active
    }
    AUTHENTICATION_ROLES {
        int roleid PK
        varchar role
    }
    AUTHENTICATION_PERMISSIONS {
        int permission_id PK
        varchar permission_name
        int roleid FK
    }
    AUTHENTICATION_USER_ROLE_MAPPINGS {
        int userid PK, FK
        int roleid PK, FK
    }

    FINANCIAL_CUSTOMERS {
        bigint customer_id PK
        varchar email
        varchar status
    }
    FINANCIAL_ACCOUNTS {
        bigint account_id PK
        bigint customer_id FK
        varchar account_type
        char currency
        varchar status
    }
    FINANCIAL_PORTFOLIOS {
        bigint portfolio_id PK
        bigint account_id FK
        varchar portfolio_name
        char base_currency
    }
    FINANCIAL_SECURITIES {
        bigint security_id PK
        varchar ticker
        varchar isin
        varchar asset_type
    }
    FINANCIAL_HOLDINGS {
        bigint holding_id PK
        bigint portfolio_id FK
        bigint security_id FK
        int quantity
        numeric average_cost
    }
    FINANCIAL_ORDERS {
        bigint order_id PK
        bigint account_id FK
        bigint security_id FK
        varchar side
        int quantity
        varchar status
    }
    FINANCIAL_EXECUTIONS {
        bigint execution_id PK
        bigint order_id FK
        int execution_quantity
        numeric execution_price
        varchar status
    }
    FINANCIAL_TRANSACTIONS {
        bigint transaction_id PK
        bigint order_id FK
        numeric gross_amount
        numeric fee_amount
        numeric net_amount
        varchar status
    }
    FINANCIAL_EXECUTION_TRANSACTIONS {
        bigint execution_id PK, FK
        bigint transaction_id PK, FK
        int allocated_quantity
        numeric allocated_amount
    }
    FINANCIAL_SETTLEMENTS {
        bigint settlement_id PK
        bigint transaction_id FK
        numeric expected_cash_amount
        numeric settled_cash_amount
        varchar status
        varchar failure_reason
    }
    FINANCIAL_CASH_MOVEMENTS {
        bigint cash_movement_id PK
        bigint settlement_id FK
        bigint account_id FK
        numeric amount
        varchar direction
        varchar status
    }

    INVESTIGATION_CASES {
        bigint investigation_id PK
        bigint settlement_id FK
        numeric expected_cash
        numeric actual_cash
        numeric discrepancy
        varchar status
        varchar investigation_type
        varchar idempotency_key
    }
    INVESTIGATION_FINDINGS {
        bigint finding_id PK
        bigint investigation_id FK
        text_array root_causes
        numeric impact
        varchar severity
        text recommended_action
    }
    INVESTIGATION_EVIDENCE {
        bigint evidence_id PK
        bigint investigation_id FK
        varchar evidence_type
        varchar source_table
        bigint source_record_id
        text evidence_text
    }
    INVESTIGATION_APPROVAL_EVENTS {
        bigint approval_event_id PK
        bigint investigation_id FK
        int actor_user_id FK
        uuid explanation_run_id FK
        varchar event_type
        varchar previous_status
        varchar new_status
        text comment
    }

    AI_POLICY_DOCUMENTS {
        bigint document_id PK
        varchar document_key
        varchar version
        varchar publication_status
        boolean is_active
        int approved_by_user_id FK
        date effective_from
        date effective_to
    }
    AI_POLICY_CHUNKS {
        bigint chunk_id PK
        bigint document_id FK
        int chunk_index
        text content
        text_array keywords
        tsvector search_vector
    }
    AI_EXPLANATION_RUNS {
        uuid run_id PK
        bigint investigation_id FK
        int requested_by_user_id FK
        varchar provider
        varchar model
        varchar prompt_version
        varchar status
        jsonb input_snapshot
        char input_sha256
        jsonb output_snapshot
        varchar error_category
    }

    AUTHENTICATION_USERS ||--o{ AUTHENTICATION_USER_ROLE_MAPPINGS : assigned
    AUTHENTICATION_ROLES ||--o{ AUTHENTICATION_USER_ROLE_MAPPINGS : maps
    AUTHENTICATION_ROLES ||--o{ AUTHENTICATION_PERMISSIONS : grants

    FINANCIAL_CUSTOMERS ||--o{ FINANCIAL_ACCOUNTS : owns
    FINANCIAL_ACCOUNTS ||--o{ FINANCIAL_PORTFOLIOS : contains
    FINANCIAL_ACCOUNTS ||--o{ FINANCIAL_ORDERS : places
    FINANCIAL_ACCOUNTS ||--o{ FINANCIAL_CASH_MOVEMENTS : records
    FINANCIAL_SECURITIES ||--o{ FINANCIAL_ORDERS : identifies
    FINANCIAL_SECURITIES ||--o{ FINANCIAL_HOLDINGS : held_as
    FINANCIAL_PORTFOLIOS ||--o{ FINANCIAL_HOLDINGS : contains
    FINANCIAL_ORDERS ||--o{ FINANCIAL_EXECUTIONS : executes_as
    FINANCIAL_ORDERS ||--o{ FINANCIAL_TRANSACTIONS : books_as
    FINANCIAL_EXECUTIONS ||--o{ FINANCIAL_EXECUTION_TRANSACTIONS : allocated_by
    FINANCIAL_TRANSACTIONS ||--o{ FINANCIAL_EXECUTION_TRANSACTIONS : allocated_by
    FINANCIAL_TRANSACTIONS ||--o{ FINANCIAL_SETTLEMENTS : settles_as
    FINANCIAL_SETTLEMENTS ||--o{ FINANCIAL_CASH_MOVEMENTS : posts

    FINANCIAL_SETTLEMENTS ||--o{ INVESTIGATION_CASES : investigated_by
    INVESTIGATION_CASES ||--o{ INVESTIGATION_FINDINGS : has
    INVESTIGATION_CASES ||--o{ INVESTIGATION_EVIDENCE : supported_by
    INVESTIGATION_CASES ||--o{ INVESTIGATION_APPROVAL_EVENTS : reviewed_through
    INVESTIGATION_CASES ||--o{ AI_EXPLANATION_RUNS : explained_by
    AUTHENTICATION_USERS ||--o{ AI_EXPLANATION_RUNS : requests
    AUTHENTICATION_USERS ||--o{ AI_POLICY_DOCUMENTS : approves
    AUTHENTICATION_USERS ||--o{ INVESTIGATION_APPROVAL_EVENTS : acts
    AI_POLICY_DOCUMENTS ||--o{ AI_POLICY_CHUNKS : split_into
    AI_EXPLANATION_RUNS o|--o{ INVESTIGATION_APPROVAL_EVENTS : may_be_linked_to
```

## How data moves through the database

1. **Financial source records** are connected by foreign keys from customer to
   account, order, execution/transaction, settlement, and cash movement. The
   broader portfolio domain also includes securities, portfolios, and
   holdings. `execution_transactions` is a composite-key allocation bridge.
2. **Reconciliation** reads a settlement and its cash movements. If expected
   and actual amounts differ, the application creates an
   `investigation.cases` row, one deterministic finding, and evidence rows.
3. **Explanation/RAG** reads the case, finding, evidence, and linked financial
   records. It retrieves only approved, active, currently effective policy
   chunks. One `ai.explanation_runs` row records each successful or failed
   provider attempt, including the input snapshot/hash and structured output
   or safe error category.
4. **Human review** moves a case from `OPEN` or `INVESTIGATING` to
   `PENDING_APPROVAL`, then to `APPROVED`, `REJECTED`, or back to
   `INVESTIGATING` for changes. The case status update and
   `investigation.approval_events` insert happen in one transaction.

## Relationship and scope notes

- The ERD draws declared database foreign keys. `investigation.evidence`
  stores `source_table` plus `source_record_id` as a polymorphic reference;
  PostgreSQL does not enforce that reference as an FK.
- `authentication.permissions` is related to roles in the database and seeded,
  but current API authorization checks the role value directly rather than
  evaluating permission rows dynamically.
- The financial, authentication, and initial investigation schemas are
  provisioned separately from the AI/approval migrations checked into this
  repository. The ERD reflects the configured live database catalog.
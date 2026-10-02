# LEDGERPILOT  AI

AI-powered Financial Operations Investigation Platform.

## Objective

Build a production-style Agentic AI system that helps
financial operations teams investigate transaction,
portfolio, settlement and cash-related issues.

## Technology

- Python
- PostgreSQL
- FastAPI
- LLM
- RAG
- Multi-Agent Architecture
- Docker
- Cloud Deployment

## Architecture diagrams

The project has audience-specific diagrams for the technical/API flow,
PostgreSQL ERD, POC workflow, and core API importance. Open the
[architecture diagram index](docs/architecture/README.md). POC and API maps
also have 16:9 vector SVGs that can be inserted into PowerPoint.
The database design is also available as an editable three-slide
[PowerPoint deck](docs/architecture/finsight-database-design.pptx).

## AI explanation audit trail

AI explanation attempts are stored in PostgreSQL in `ai.explanation_runs`.
The audit rows capture the requesting user, investigation, provider/model,
prompt version, a structured input snapshot and SHA-256 hash, outcome, duration,
and structured output or a safe failure category. The database trigger blocks
updates, deletes, and truncation of audit rows.

Apply `scripts/migrations/ai.explanation_runs.sql` after the investigation and
authentication schemas have been created:

```powershell
psql -h localhost -U postgres -d finsight -f scripts/migrations/ai.explanation_runs.sql
```

To inspect run metadata without selecting the stored financial snapshots:

```sql
SELECT
	run_id,
	investigation_id,
	requested_by_user_id,
	provider,
	model,
	status,
	error_category,
	duration_ms,
	started_at,
	completed_at
FROM ai.explanation_runs
ORDER BY created_at DESC;
```

The API uses a separate database connection for audit writes, so recording an
AI result does not commit or modify the financial read transaction.

## Policy retrieval (RAG)

The explanation agent retrieves approved and currently effective policy chunks
from PostgreSQL using English full-text search and curated keywords. Matching
chunks are included in the explanation input and audit snapshot. The LLM may
return preventive actions only with citations that exactly match retrieved
policy references. This first version is lexical RAG; it does not use vector
embeddings and may miss semantically related wording.

After the core financial and authentication schemas exist, apply:

```powershell
psql -h localhost -U postgres -d finsight -f scripts/migrations/ai.policy_documents.sql
psql -h localhost -U postgres -d finsight -f scripts/seed_ai_policy_examples.sql
```

The seeded policies are demonstration examples, not legal, regulatory, or
production operating guidance. Replace them with documents reviewed and
approved by your organization before using the recommendations operationally.

## Human approval workflow

Apply `scripts/migrations/investigation.approval_events.sql` after the
investigation, authentication, and AI explanation audit schemas exist. Each
workflow transition updates the investigation and appends its approval event
inside one PostgreSQL transaction. Database triggers prevent event updates,
deletes, and truncation.

The analyst or reviewer submits a case for review:

```http
POST /investigations/{investigation_id}/submit-for-approval
```

```json
{
	"comment": "Please review the evidence and proposed action.",
	"explanation_run_id": "optional UUID returned by the explanation API"
}
```

The explanation run ID is optional, but when supplied it must identify a
successful explanation for this same investigation. A reviewer or
administrator then decides:

```http
POST /investigations/{investigation_id}/decision
```

```json
{
	"decision": "APPROVE",
	"comment": "Evidence reviewed and approved."
}
```

Supported decisions are `APPROVE`, `REJECT`, and `REQUEST_CHANGES`. Requesting
changes returns the case to `INVESTIGATING`; it can then be submitted again.
The original submitter cannot approve their own submission. Read the full
history with `GET /investigations/{investigation_id}/approval-events`. The old
generic status-update endpoint is deprecated and returns `409` so it cannot
bypass the approval event trail.
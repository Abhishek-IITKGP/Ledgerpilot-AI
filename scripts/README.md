# Database Setup Scripts

This directory is intentionally limited to PostgreSQL schema migrations and
reusable reference/lookup data. Scenario-specific financial sample rows,
sample policy content, and document-generator utilities are not part of this
database setup set.

## Prerequisites

The base `financial` and `authentication` schemas/tables are managed separately
and are not fully defined by the migrations in this repository. Provision those
schemas first. The migrations below add the investigation and AI workflow
tables; they do not initialize a database from zero.

## Apply order

Run from the repository root, using your configured PostgreSQL connection:

```powershell
psql -h localhost -U postgres -d finsight -f scripts/migrations/authentication.extensions.sql
psql -h localhost -U postgres -d finsight -f scripts/migrations/investigation.cases.sql
psql -h localhost -U postgres -d finsight -f scripts/migrations/investigation.findings.sql
psql -h localhost -U postgres -d finsight -f scripts/migrations/investigation.evidence.sql
psql -h localhost -U postgres -d finsight -f scripts/migrations/ai.explanation_runs.sql
psql -h localhost -U postgres -d finsight -f scripts/migrations/ai.policy_documents.sql
psql -h localhost -U postgres -d finsight -f scripts/migrations/investigation.approval_events.sql
psql -h localhost -U postgres -d finsight -f scripts/seeds/reference/authentication_roles_permissions.sql
```

The roles/permissions seed contains reusable lookup data only. It deliberately
does not create users or assign shared default passwords. Provision the first
administrator through a secure bootstrap procedure; then create other users
with `POST /auth/users`.

Scenario-specific financial rows and demonstration policy content are
intentionally excluded from this database setup set. They are not reusable
lookup data and should not be loaded as production reference values.
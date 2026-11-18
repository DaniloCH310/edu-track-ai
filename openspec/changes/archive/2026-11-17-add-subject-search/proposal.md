# Change: Academic subject search (Task 14)

## Why

Task 14 requests subjects searchable by name or by overdue tasks. Task search does
not fulfill this requirement. This proposal is recorded before its implementation.

## What Changes

- Extend GET /api/subjects with optional query and overdue parameters.
- Match a literal name substring case-insensitively; trim whitespace.
- overdue=true means at least one non-completed task due before today in
  America/Sao_Paulo. False/omitted leaves this filter disabled.
- Combine supplied filters with AND and always enforce ownership.
- Preserve response schema, ordering and existing frontend behavior.

## Impact

Only the subjects route/repository, tests and documentation change. No migration,
new dependencies, frontend changes, external calls or separate search service.
Use EXISTS to avoid duplicates. Validate locally with disposable in-memory SQLite
and PostgreSQL SQL compilation; real PostgreSQL execution remains a CI check.
Academic evidence uses FastAPI Swagger and Python/SQLAlchemy in place of Xano.

## Project profile

EduTrack AI is an academic organization application with a FastAPI and
SQLAlchemy backend, PostgreSQL database, Alembic migrations, and a frontend
written in HTML, CSS, and JavaScript. FastAPI serves the frontend from
`app/static/` and exposes the HTTP API under `/api`. Xano and FlutterFlow are
not part of this implementation.

## Architecture and scope

- Keep HTTP routes in `app/api/`, business rules in `app/services/`, database
  access in `app/repositories/`, SQLAlchemy entities in `app/models/`, and
  request/response contracts in `app/schemas/`.
- Preserve the application factory and real entry point in `app/main.py`.
- Keep frontend modules in `app/static/js/`, visual styles in
  `app/static/css/`, and shared design tokens in `app/static/css/tokens.css`.
- Implement only the behavior requested. Avoid unrelated refactors,
  infrastructure changes, or new dependencies.

## Security and data isolation

- Every query for academic data MUST be scoped to the authenticated user.
- Never log or commit passwords, reset tokens, JWT secrets, OAuth credentials,
  SMTP credentials, Gemini keys, cookies, or Google Classroom tokens.
- Preserve neutral public responses in password recovery and existing request
  limits around authentication and external AI calls.
- Do not run destructive database operations unless the configured database is
  explicitly authorized as disposable by the protections in
  `tests/database_safety.py`.

## Development and validation

- Use English for Python and JavaScript identifiers; user-facing copy may be
  written in Brazilian Portuguese.
- Add or update focused tests for behavior changes. Prefer unit tests when a
  database is not required.
- Run Ruff for changed Python modules and validate all OpenSpec specifications.
- PostgreSQL tests may run only against the dedicated disposable test database
  or the isolated database created by GitHub Actions.
- Keep the frontend accessible without animation and preserve readable text for
  progress, status, and navigation.

## OpenSpec workflow

- Read the canonical specification in `openspec/specs/` before changing a
  capability.
- For a new behavior, create a proposal, delta specification, and verifiable
  task list under `openspec/changes/` before implementation.
- Use `ADDED`, `MODIFIED`, or `REMOVED Requirements` in delta specifications,
  and give every requirement at least one `WHEN`/`THEN` scenario.
- After implementation and validation, update the canonical specification and
  archive the completed change under `openspec/changes/archive/`.
- Never describe a retrospective specification as if it preceded earlier code.

## Git and delivery

- Use isolated branches or worktrees with prefixes such as `feat/`, `fix/`,
  `docs/`, or `release/`.
- Follow Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).
- Review the diff before committing and keep unrelated Graphify output or local
  configuration out of feature commits.
- Do not force-push, deploy production, merge Pull Requests, or delete data
  without explicit user authorization.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

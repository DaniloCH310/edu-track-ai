# Delivery and Portability Delta

## ADDED Requirements

### Requirement: Verifiable agent instructions

The repository SHALL keep a root `AGENTS.md` that documents the real architecture, scope limits, user isolation, database safety, validation, OpenSpec workflow and Git conventions while preserving existing specialist instructions.

#### Scenario: Agent starts a change

- **WHEN** an agent reads `AGENTS.md` before changing the project
- **THEN** it can identify the FastAPI entry point, layer boundaries and required checks

#### Scenario: Sensitive operation

- **WHEN** work touches databases, secrets, production or Git integration
- **THEN** the agent avoids real data, destructive actions, force push, deployment and merge without explicit authorization

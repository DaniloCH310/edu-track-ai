## ADDED Requirements

### Requirement: Academic subject search

The system SHALL extend authenticated GET /api/subjects with optional query
(maximum 160 characters) and overdue (boolean, default false). query SHALL match
a literal case-insensitive substring of the subject name after trimming; empty
input SHALL disable the name filter. Percent and underscore SHALL be literal.
overdue=true SHALL require an existing non-completed task whose due_date is before
today in America/Sao_Paulo. Supplied filters SHALL combine with AND. Responses
SHALL retain the existing schema and alphabetical ordering, contain only owned
subjects and SHALL NOT duplicate subjects.

#### Scenario: Name search
- **WHEN** an authenticated student searches a name with different letter case
- **THEN** only their matching subjects are returned; an unknown name returns []

#### Scenario: Overdue boundaries
- **WHEN** overdue=true is supplied
- **THEN** subjects with one or many overdue pending/in-progress tasks appear once
- **AND** completed overdue tasks, tasks due today or later and subjects without tasks do not qualify

#### Scenario: Combined filters and privacy
- **WHEN** query and overdue=true are supplied
- **THEN** a subject must satisfy both filters and belong to the authenticated user

#### Scenario: Backward compatibility
- **WHEN** filters are omitted, or query is blank and overdue is false
- **THEN** the existing owned-subject list, ordering and response schema are preserved

#### Scenario: Invalid or unauthenticated request
- **WHEN** the query exceeds 160 characters or overdue is not a valid boolean
- **THEN** the API returns 422
- **AND** requests without a valid session remain unauthorized

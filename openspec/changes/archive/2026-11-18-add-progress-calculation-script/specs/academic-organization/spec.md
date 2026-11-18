# Academic Organization Delta

## ADDED Requirements

### Requirement: Reusable progress calculation

The project SHALL provide a Python function that accepts integer completed and total task counts, validates the values and returns JSON containing the rounded integer percentage using the same rule as the dashboard.

#### Scenario: Common progress

- **WHEN** the function receives 3 completed tasks out of 5
- **THEN** it returns `{"percentage": 60}`

#### Scenario: No tasks

- **WHEN** the function receives zero completed tasks and zero total tasks
- **THEN** it returns `{"percentage": 0}` without division by zero

#### Scenario: Invalid counts

- **WHEN** counts are negative, non-integer or completed exceeds total
- **THEN** the function rejects the input with a validation error

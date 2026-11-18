# Change: Add a reusable progress calculation script

## Why

Task 12 requires a verifiable Python function that calculates academic progress, returns JSON and handles division by zero. The dashboard already owns the canonical percentage rule, but it is not exposed as a small command-line demonstration.

## What Changes

- Add a pure progress calculation function that reuses the dashboard percentage rule.
- Accept a JSON object on standard input and return a JSON result.
- Validate missing, negative, non-integer and inconsistent task counts.
- Cover common values, zero tasks, invalid values and the JSON command interface with unit tests.

## Impact

- Adds a pure shared progress helper, `scripts/calculate_progress.py` and focused unit tests.
- Does not change database schema, API routes or dashboard behavior.

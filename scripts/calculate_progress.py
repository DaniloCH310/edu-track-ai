"""Calculate academic progress from a small JSON payload.

Input example::

    {"completed_tasks": 3, "total_tasks": 5}

The command writes ``{"percentage": 60}`` to standard output.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from typing import Any

from app.services.progress import percentage


def calculate_progress(completed_tasks: int, total_tasks: int) -> dict[str, int]:
    """Return the rounded completion percentage after validating task counts."""
    if isinstance(completed_tasks, bool) or not isinstance(completed_tasks, int):
        raise ValueError("completed_tasks must be an integer")
    if isinstance(total_tasks, bool) or not isinstance(total_tasks, int):
        raise ValueError("total_tasks must be an integer")
    if completed_tasks < 0 or total_tasks < 0:
        raise ValueError("task counts cannot be negative")
    if completed_tasks > total_tasks:
        raise ValueError("completed_tasks cannot exceed total_tasks")
    return {"percentage": percentage(completed_tasks, total_tasks)}


def calculate_from_payload(payload: Mapping[str, Any]) -> dict[str, int]:
    """Validate a JSON-like payload and calculate its progress."""
    try:
        completed_tasks = payload["completed_tasks"]
        total_tasks = payload["total_tasks"]
    except KeyError as exc:
        raise ValueError(f"missing field: {exc.args[0]}") from exc
    return calculate_progress(completed_tasks, total_tasks)


def main() -> int:
    """Read one JSON object from stdin and write the calculated JSON result."""
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("input must be a JSON object")
        print(json.dumps(calculate_from_payload(payload), ensure_ascii=False))
    except (json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

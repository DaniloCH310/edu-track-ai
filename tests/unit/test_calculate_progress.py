import json
import subprocess
import sys

import pytest

from scripts.calculate_progress import calculate_from_payload, calculate_progress


@pytest.mark.parametrize(
    ("completed", "total", "expected"),
    [(3, 5, 60), (1, 3, 33), (2, 3, 67), (5, 5, 100), (0, 5, 0)],
)
def test_calculate_progress_common_values(completed: int, total: int, expected: int) -> None:
    assert calculate_progress(completed, total) == {"percentage": expected}


def test_calculate_progress_without_tasks_returns_zero() -> None:
    assert calculate_progress(0, 0) == {"percentage": 0}


@pytest.mark.parametrize("completed,total", [(-1, 1), (1, -1), (2, 1), (True, 1)])
def test_calculate_progress_rejects_invalid_counts(completed: int, total: int) -> None:
    with pytest.raises(ValueError):
        calculate_progress(completed, total)


def test_calculate_from_payload_requires_both_fields() -> None:
    with pytest.raises(ValueError, match="missing field: total_tasks"):
        calculate_from_payload({"completed_tasks": 1})


def test_module_accepts_and_returns_json() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "scripts.calculate_progress"],
        input=json.dumps({"completed_tasks": 3, "total_tasks": 4}),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout) == {"percentage": 75}
    assert result.stderr == ""

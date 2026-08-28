from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models import TaskStatus
from app.schemas.subject import SubjectCreate
from app.schemas.task import TaskCreate


def test_subject_normalizes_text_and_accepts_a_valid_date_range():
    """Catches whitespace leaking into stored subject identity fields."""
    payload = SubjectCreate(
        name="  Python Aplicado ",
        professor="  Marina Costa ",
        workload_hours=80,
        description="  Lógica e dados. ",
        period=" 2026.2 ",
        color="#6750a4",
        start_date=date(2026, 8, 1),
        end_date=date(2026, 12, 15),
    )

    assert payload.name == "Python Aplicado"
    assert payload.professor == "Marina Costa"
    assert payload.description == "Lógica e dados."
    assert payload.period == "2026.2"
    assert payload.color == "#6750A4"


@pytest.mark.parametrize(
    "changes",
    [
        {"workload_hours": 0},
        {"color": "roxo"},
        {"start_date": date(2026, 12, 15), "end_date": date(2026, 8, 1)},
    ],
)
def test_subject_rejects_invalid_workload_color_or_date_range(changes):
    """Catches invalid subject data reaching the database constraints."""
    values = {
        "name": "Python Aplicado",
        "workload_hours": 80,
        "color": "#6750A4",
        "start_date": date(2026, 8, 1),
        "end_date": date(2026, 12, 15),
    }
    values.update(changes)

    with pytest.raises(ValidationError):
        SubjectCreate(**values)


def test_task_normalizes_title_and_uses_canonical_status():
    """Catches blank-padded titles or translated status values in persistence."""
    payload = TaskCreate(
        subject_id=uuid4(),
        title="  Finalizar exercício  ",
        description="  Resolver a lista 3. ",
        due_date=date(2026, 9, 1),
        status=TaskStatus.IN_PROGRESS,
    )

    assert payload.title == "Finalizar exercício"
    assert payload.description == "Resolver a lista 3."
    assert payload.status is TaskStatus.IN_PROGRESS


def test_task_rejects_blank_title():
    """Catches academic tasks without an actionable title."""
    with pytest.raises(ValidationError):
        TaskCreate(
            subject_id=uuid4(),
            title="   ",
            due_date=date(2026, 9, 1),
            status=TaskStatus.PENDING,
        )

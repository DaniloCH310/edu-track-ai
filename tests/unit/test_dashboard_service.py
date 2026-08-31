from datetime import date, timedelta
from uuid import uuid4

from app.models import AcademicTask, Subject, TaskStatus
from app.services.dashboard import calculate_dashboard


def test_dashboard_calculates_progress_deadlines_and_upcoming_items():
    """Catches incorrect denominators and deadline boundary mistakes in student metrics."""
    today = date(2026, 8, 27)
    python_id = uuid4()
    ux_id = uuid4()
    subjects = [
        Subject(id=python_id, user_id=uuid4(), name="Python", workload_hours=80),
        Subject(id=ux_id, user_id=uuid4(), name="UX", workload_hours=60),
    ]
    tasks = [
        AcademicTask(
            subject_id=python_id,
            title="Concluída",
            due_date=today,
            status=TaskStatus.COMPLETED,
        ),
        AcademicTask(
            subject_id=python_id,
            title="Hoje",
            due_date=today,
            status=TaskStatus.PENDING,
        ),
        AcademicTask(
            subject_id=ux_id,
            title="Em três dias",
            due_date=today + timedelta(days=3),
            status=TaskStatus.IN_PROGRESS,
        ),
        AcademicTask(
            subject_id=ux_id,
            title="Atrasada",
            due_date=today - timedelta(days=1),
            status=TaskStatus.PENDING,
        ),
        AcademicTask(
            subject_id=ux_id,
            title="Distante",
            due_date=today + timedelta(days=10),
            status=TaskStatus.PENDING,
        ),
    ]

    dashboard = calculate_dashboard(subjects, tasks, today)

    assert dashboard.total_tasks == 5
    assert dashboard.completed_tasks == 1
    assert dashboard.overall_progress == 20
    assert dashboard.due_soon == 2
    assert dashboard.overdue == 1
    assert [(item.subject_name, item.progress) for item in dashboard.progress_by_subject] == [
        ("Python", 50),
        ("UX", 0),
    ]
    assert [item.title for item in dashboard.upcoming] == [
        "Atrasada",
        "Hoje",
        "Em três dias",
        "Distante",
    ]


def test_dashboard_is_zeroed_when_there_are_no_tasks():
    """Catches division by zero and misleading empty-state percentages."""
    subject = Subject(id=uuid4(), user_id=uuid4(), name="Python", workload_hours=80)

    dashboard = calculate_dashboard([subject], [], date(2026, 8, 27))

    assert dashboard.total_tasks == 0
    assert dashboard.overall_progress == 0
    assert dashboard.progress_by_subject[0].progress == 0
    assert dashboard.upcoming == []


def test_dashboard_recommends_overdue_task_before_nearer_future_work():
    """Catches a study plan that lets a future deadline outrank overdue work."""
    today = date(2026, 8, 27)
    subject_id = uuid4()
    subjects = [Subject(id=subject_id, user_id=uuid4(), name="Python", workload_hours=80)]
    tasks = [
        AcademicTask(
            subject_id=subject_id,
            title="Entrega amanhã",
            due_date=today + timedelta(days=1),
            status=TaskStatus.PENDING,
        ),
        AcademicTask(
            subject_id=subject_id,
            title="Atividade atrasada",
            due_date=today - timedelta(days=1),
            status=TaskStatus.PENDING,
        ),
    ]

    dashboard = calculate_dashboard(subjects, tasks, today)

    assert dashboard.recommended_task.title == "Atividade atrasada"
    assert dashboard.recommended_task.priority == "urgent"
    assert "atrasada" in dashboard.recommended_task.reason.casefold()


def test_dashboard_uses_lower_subject_progress_to_break_future_deadline_ties():
    """Catches a plan that ignores a discipline needing more attention."""
    today = date(2026, 8, 27)
    advanced_id, starting_id = uuid4(), uuid4()
    subjects = [
        Subject(id=advanced_id, user_id=uuid4(), name="Avançada", workload_hours=80),
        Subject(id=starting_id, user_id=uuid4(), name="Em início", workload_hours=80),
    ]
    tasks = [
        AcademicTask(
            subject_id=advanced_id,
            title="Finalizar revisão",
            due_date=today + timedelta(days=8),
            status=TaskStatus.PENDING,
        ),
        AcademicTask(
            subject_id=advanced_id,
            title="Já concluída",
            due_date=today,
            status=TaskStatus.COMPLETED,
        ),
        AcademicTask(
            subject_id=starting_id,
            title="Começar leitura",
            due_date=today + timedelta(days=8),
            status=TaskStatus.PENDING,
        ),
    ]

    dashboard = calculate_dashboard(subjects, tasks, today)

    assert dashboard.recommended_task.title == "Começar leitura"
    assert dashboard.recommended_task.priority == "routine"
    assert "0%" in dashboard.recommended_task.reason


def test_dashboard_has_no_recommendation_without_pending_tasks():
    subject = Subject(id=uuid4(), user_id=uuid4(), name="Python", workload_hours=80)
    task = AcademicTask(
        subject_id=subject.id,
        title="Concluída",
        due_date=date(2026, 8, 27),
        status=TaskStatus.COMPLETED,
    )

    dashboard = calculate_dashboard([subject], [task], date(2026, 8, 27))

    assert dashboard.recommended_task is None

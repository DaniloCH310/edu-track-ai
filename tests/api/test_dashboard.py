from datetime import date, timedelta

from app.models.subject import Subject
from app.models.task import AcademicTask, TaskStatus


def test_dashboard_metrics_are_user_scoped(client, user_factory, db_session):
    user = user_factory(email="ana@example.com")
    other = user_factory(email="outra@example.com")
    subjects = [
        Subject(user_id=user.id, name="Python Aplicado", workload_hours=80, color="#6750A4"),
        Subject(user_id=user.id, name="UX e Interfaces", workload_hours=60, color="#00796B"),
        Subject(user_id=user.id, name="Banco de Dados", workload_hours=60, color="#E67E22"),
    ]
    foreign = Subject(
        user_id=other.id, name="Disciplina alheia", workload_hours=20, color="#000000"
    )
    db_session.add_all([*subjects, foreign])
    db_session.flush()
    today = date.today()
    db_session.add_all(
        [
            AcademicTask(
                subject_id=subjects[0].id,
                title="Concluída Python",
                due_date=today,
                status=TaskStatus.COMPLETED,
            ),
            AcademicTask(
                subject_id=subjects[0].id,
                title="Hoje",
                due_date=today,
                status=TaskStatus.PENDING,
            ),
            AcademicTask(
                subject_id=subjects[1].id,
                title="Em três dias",
                due_date=today + timedelta(days=3),
                status=TaskStatus.IN_PROGRESS,
            ),
            AcademicTask(
                subject_id=subjects[2].id,
                title="Atrasada",
                due_date=today - timedelta(days=1),
                status=TaskStatus.PENDING,
            ),
            AcademicTask(
                subject_id=subjects[2].id,
                title="Concluída Banco",
                due_date=today - timedelta(days=2),
                status=TaskStatus.COMPLETED,
            ),
            AcademicTask(
                subject_id=foreign.id,
                title="Não pode vazar",
                due_date=today,
                status=TaskStatus.PENDING,
            ),
        ]
    )
    db_session.commit()
    assert client.post(
        "/api/auth/login",
        json={"email": user.email, "password": "Senha-Forte-123"},
    ).status_code == 200

    response = client.get("/api/dashboard")

    assert response.status_code == 200
    data = response.json()
    assert data["total_subjects"] == 3
    assert data["total_tasks"] == 5
    assert data["completed_tasks"] == 2
    assert data["overall_progress"] == 40
    assert data["due_soon"] == 2
    assert data["overdue"] == 1
    assert [item["subject_name"] for item in data["progress_by_subject"]] == [
        "Banco de Dados",
        "Python Aplicado",
        "UX e Interfaces",
    ]
    assert [item["title"] for item in data["upcoming"]] == [
        "Atrasada",
        "Hoje",
        "Em três dias",
    ]

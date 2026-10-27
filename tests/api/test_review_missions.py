from datetime import UTC, date, datetime, timedelta

from app.models.review_mission import ReviewMission, ReviewMissionStatus
from app.models.subject import Subject
from app.models.task import AcademicTask, TaskStatus


def login(client, email: str) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "Senha-Forte-123"},
    )
    assert response.status_code == 200


def make_subject(db_session, user_id) -> Subject:
    subject = Subject(
        user_id=user_id,
        name="Banco de Dados",
        workload_hours=60,
        color="#6750A4",
    )
    db_session.add(subject)
    db_session.commit()
    db_session.refresh(subject)
    return subject


def test_completed_task_schedules_review_and_reopening_removes_pending_mission(
    client, user_factory, db_session
):
    user = user_factory(email="reviews@example.com")
    subject = make_subject(db_session, user.id)
    login(client, user.email)

    created = client.post(
        "/api/tasks",
        json={
            "subject_id": str(subject.id),
            "title": "Modelar o banco",
            "due_date": str(date.today()),
            "status": "pending",
        },
    )
    task_id = created.json()["id"]
    assert client.patch(
        f"/api/tasks/{task_id}/status", json={"status": "completed"}
    ).status_code == 200

    missions = client.get("/api/reviews").json()
    assert len(missions) == 1
    assert missions[0]["task_id"] == task_id
    assert missions[0]["status"] == "pending"
    assert missions[0]["due_date"] == str(date.today() + timedelta(days=3))
    assert missions[0]["is_available"] is False

    assert client.patch(
        f"/api/tasks/{task_id}/status", json={"status": "in_progress"}
    ).status_code == 200
    assert client.get("/api/reviews").json() == []


def test_available_review_has_three_questions_and_records_mastery(
    client, user_factory, db_session
):
    user = user_factory(email="mastery@example.com")
    subject = make_subject(db_session, user.id)
    task = AcademicTask(
        subject_id=subject.id,
        title="Normalizar tabelas",
        description="Aplicar primeira, segunda e terceira forma normal.",
        due_date=date.today() - timedelta(days=3),
        status=TaskStatus.COMPLETED,
        completed_at=datetime.now(UTC) - timedelta(days=3),
    )
    db_session.add(task)
    db_session.flush()
    mission = ReviewMission(
        task_id=task.id,
        subject_id=subject.id,
        due_date=date.today(),
        status=ReviewMissionStatus.PENDING,
    )
    db_session.add(mission)
    db_session.commit()
    login(client, user.email)

    started = client.post(f"/api/reviews/{mission.id}/start")
    assert started.status_code == 200
    assert started.json()["status"] == "in_progress"
    assert len(started.json()["questions"]) == 3

    completed = client.post(
        f"/api/reviews/{mission.id}/submit",
        json={
            "answers": [
                "O objetivo é reduzir redundância e manter os dados consistentes em cada tabela.",
                "As chaves e dependências funcionais orientam a separação correta das informações.",
                "Eu criaria tabelas relacionadas para clientes, pedidos e itens "
                "sem repetir atributos.",
            ]
        },
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"
    assert completed.json()["mastery_percent"] >= 55
    assert completed.json()["mastery_summary"]

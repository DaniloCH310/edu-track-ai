from datetime import UTC, date, datetime, timedelta
from uuid import UUID

import pytest

from app.models.review_mission import ReviewMission, ReviewMissionStatus
from app.models.subject import Subject
from app.models.task import AcademicTask, TaskStatus


@pytest.fixture(params=[
    (datetime(2026, 11, 18, 0, 0, tzinfo=UTC), date(2026, 11, 17)),
    (datetime(2026, 11, 18, 2, 59, 59, tzinfo=UTC), date(2026, 11, 17)),
    (datetime(2026, 11, 18, 3, 0, tzinfo=UTC), date(2026, 11, 18)),
], ids=["utc-midnight", "before-sao-paulo-midnight", "sao-paulo-midnight"])
def review_clock(request, monkeypatch):
    """Control only review-related clocks; leave authentication token clocks real."""
    from app.api import review_missions
    from app.repositories import tasks

    instant, academic_day = request.param

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return instant.astimezone(tz) if tz else instant.replace(tzinfo=None)

    class FixedDate(date):
        @classmethod
        def today(cls):
            return academic_day

    monkeypatch.setattr(tasks, "datetime", FixedDateTime)
    monkeypatch.setattr(review_missions, "date", FixedDate)
    return instant, academic_day


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
    client, user_factory, db_session, review_clock
):
    instant, academic_day = review_clock
    user = user_factory(email="reviews@example.com")
    subject = make_subject(db_session, user.id)
    login(client, user.email)

    created = client.post(
        "/api/tasks",
        json={
            "subject_id": str(subject.id),
            "title": "Modelar o banco",
            "due_date": str(academic_day),
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
    db_session.expire_all()
    assert db_session.get(AcademicTask, UUID(missions[0]["task_id"])).completed_at == instant
    assert missions[0]["due_date"] == str(academic_day + timedelta(days=3))
    assert missions[0]["is_available"] is False

    assert client.patch(
        f"/api/tasks/{task_id}/status", json={"status": "in_progress"}
    ).status_code == 200
    assert client.get("/api/reviews").json() == []


def test_available_review_has_three_questions_and_records_mastery(
    client, user_factory, db_session, review_clock
):
    instant, academic_day = review_clock
    user = user_factory(email="mastery@example.com")
    subject = make_subject(db_session, user.id)
    task = AcademicTask(
        subject_id=subject.id,
        title="Normalizar tabelas",
        description="Aplicar primeira, segunda e terceira forma normal.",
        due_date=academic_day - timedelta(days=3),
        status=TaskStatus.COMPLETED,
        completed_at=instant - timedelta(days=3),
    )
    db_session.add(task)
    db_session.flush()
    mission = ReviewMission(
        task_id=task.id,
        subject_id=subject.id,
        due_date=academic_day,
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
    assert completed.json()["mastery_percent"] is None
    assert "ainda não foi avaliado" in completed.json()["mastery_summary"]
    assert completed.json()["mastery_summary"]

from datetime import date

from app.models.subject import Subject
from app.models.task import AcademicTask, TaskStatus
from app.repositories.classroom import ClassroomRepository


def login(client, email: str) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "Senha-Forte-123"},
    )
    assert response.status_code == 200


def make_subject(db_session, user_id, name="Python Aplicado") -> Subject:
    subject = Subject(
        user_id=user_id,
        name=name,
        workload_hours=80,
        color="#6750A4",
    )
    db_session.add(subject)
    db_session.commit()
    db_session.refresh(subject)
    return subject


def task_payload(subject_id, **overrides):
    payload = {
        "subject_id": str(subject_id),
        "title": "Finalizar exercício",
        "description": "Resolver a lista 3.",
        "due_date": "2026-09-01",
        "status": "pending",
    }
    payload.update(overrides)
    return payload


def test_task_crud_and_completion_timestamp(client, user_factory, db_session):
    user = user_factory(email="ana@example.com")
    subject = make_subject(db_session, user.id)
    login(client, user.email)

    created = client.post("/api/tasks", json=task_payload(subject.id))

    assert created.status_code == 201
    task_id = created.json()["id"]
    assert created.json()["subject_name"] == "Python Aplicado"
    assert created.json()["source"] == "local"
    assert created.json()["external_url"] is None
    completed = client.patch(
        f"/api/tasks/{task_id}/status", json={"status": "completed"}
    )
    assert completed.status_code == 200
    assert completed.json()["completed_at"] is not None

    reopened = client.patch(
        f"/api/tasks/{task_id}/status", json={"status": "in_progress"}
    )
    assert reopened.json()["completed_at"] is None
    updated = client.put(
        f"/api/tasks/{task_id}",
        json=task_payload(subject.id, title="Finalizar projeto", due_date="2026-09-05"),
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Finalizar projeto"
    assert client.get(f"/api/tasks/{task_id}").status_code == 200
    assert client.delete(f"/api/tasks/{task_id}").status_code == 204
    assert client.get(f"/api/tasks/{task_id}").status_code == 404


def test_classroom_task_exposes_safe_link_without_secret(
    client, user_factory, db_session
):
    user = user_factory(email="classroom-task@example.com")
    subject = make_subject(db_session, user.id)
    task = AcademicTask(
        subject_id=subject.id,
        title="Atividade importada",
        due_date=date(2026, 9, 20),
    )
    db_session.add(task)
    db_session.flush()
    connection = ClassroomRepository.upsert_connection(
        db_session, user.id, "encrypted-not-returned", "readonly-scopes"
    )
    course_link = ClassroomRepository.create_course_link(
        db_session, connection.id, subject.id, "course-1", "ACTIVE"
    )
    ClassroomRepository.create_task_link(
        db_session,
        course_link.id,
        task.id,
        "work-1",
        "submission-1",
        "https://classroom.google.com/c/example",
        None,
    )
    db_session.commit()
    login(client, user.email)

    payload = client.get(f"/api/tasks/{task.id}").json()

    assert payload["source"] == "google_classroom"
    assert payload["external_url"] == "https://classroom.google.com/c/example"
    assert "encrypted" not in str(payload).lower()


def test_task_cannot_use_or_expose_another_users_subject(
    client, user_factory, db_session
):
    owner = user_factory(email="dona@example.com")
    intruder = user_factory(email="ana@example.com")
    foreign_subject = make_subject(db_session, owner.id, "Banco de Dados")
    foreign_task = AcademicTask(
        subject_id=foreign_subject.id,
        title="Modelar tabelas",
        due_date=date(2026, 9, 2),
    )
    db_session.add(foreign_task)
    db_session.commit()
    login(client, intruder.email)

    assert client.post(
        "/api/tasks", json=task_payload(foreign_subject.id)
    ).status_code == 404
    assert client.get(f"/api/tasks/{foreign_task.id}").status_code == 404
    assert client.put(
        f"/api/tasks/{foreign_task.id}", json=task_payload(foreign_subject.id)
    ).status_code == 404
    assert client.delete(f"/api/tasks/{foreign_task.id}").status_code == 404
    assert client.get("/api/tasks").json() == []


def test_task_filters_search_and_order_are_composable(
    client, user_factory, db_session
):
    user = user_factory(email="ana@example.com")
    python = make_subject(db_session, user.id, "Python Aplicado")
    ux = make_subject(db_session, user.id, "UX e Interfaces")
    db_session.add_all(
        [
            AcademicTask(
                subject_id=python.id,
                title="Exercício de listas",
                description="Praticar Python",
                due_date=date(2026, 9, 3),
                status=TaskStatus.PENDING,
            ),
            AcademicTask(
                subject_id=python.id,
                title="Projeto final",
                description="API FastAPI",
                due_date=date(2026, 9, 8),
                status=TaskStatus.IN_PROGRESS,
            ),
            AcademicTask(
                subject_id=ux.id,
                title="Protótipo navegável",
                description="Fluxo no Figma",
                due_date=date(2026, 9, 1),
                status=TaskStatus.COMPLETED,
            ),
        ]
    )
    db_session.commit()
    login(client, user.email)

    searched = client.get("/api/tasks", params={"query": "fastapi"}).json()
    assert [item["title"] for item in searched] == ["Projeto final"]
    pending = client.get("/api/tasks", params={"status": "pending"}).json()
    assert [item["title"] for item in pending] == ["Exercício de listas"]
    ux_only = client.get(
        "/api/tasks", params={"subject_id": str(ux.id)}
    ).json()
    assert [item["title"] for item in ux_only] == ["Protótipo navegável"]
    descending = client.get("/api/tasks", params={"order": "due_desc"}).json()
    assert [item["due_date"] for item in descending] == [
        "2026-09-08",
        "2026-09-03",
        "2026-09-01",
    ]
    ascending = client.get("/api/tasks", params={"order": "due_asc"}).json()
    assert [item["due_date"] for item in ascending] == [
        "2026-09-01",
        "2026-09-03",
        "2026-09-08",
    ]
    newest = client.get("/api/tasks", params={"order": "created_desc"}).json()
    assert [item["title"] for item in newest] == [
        "Protótipo navegável",
        "Projeto final",
        "Exercício de listas",
    ]
    assert client.get("/api/tasks", params={"status": "inexistente"}).status_code == 422

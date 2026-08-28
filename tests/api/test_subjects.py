from datetime import date

from sqlalchemy import select

from app.models.subject import Subject
from app.models.task import AcademicTask


def login(client, *, email: str, password: str = "Senha-Forte-123") -> None:
    response = client.post(
        "/api/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200


def subject_payload(**overrides):
    payload = {
        "name": "Python Aplicado",
        "professor": "Prof. Marina",
        "workload_hours": 80,
        "description": "Programação aplicada a dados.",
        "period": "2026.2",
        "color": "#6750A4",
        "start_date": "2026-08-10",
        "end_date": "2026-12-18",
    }
    payload.update(overrides)
    return payload


def test_subject_crud_is_scoped_to_authenticated_user(client, user_factory):
    user_factory(email="ana@example.com")
    login(client, email="ana@example.com")

    created = client.post("/api/subjects", json=subject_payload())

    assert created.status_code == 201
    subject_id = created.json()["id"]
    assert created.json()["name"] == "Python Aplicado"
    assert created.json()["color"] == "#6750A4"
    assert client.get("/api/subjects").json()[0]["id"] == subject_id

    updated = client.put(
        f"/api/subjects/{subject_id}",
        json=subject_payload(name="Python e Dados", color="#00796b"),
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Python e Dados"
    assert updated.json()["color"] == "#00796B"
    assert client.get(f"/api/subjects/{subject_id}").status_code == 200
    assert client.delete(f"/api/subjects/{subject_id}").status_code == 204
    assert client.get(f"/api/subjects/{subject_id}").status_code == 404


def test_subject_validation_rejects_invalid_business_fields(client, user_factory):
    user_factory(email="ana@example.com")
    login(client, email="ana@example.com")

    invalid_payloads = [
        subject_payload(name="   "),
        subject_payload(workload_hours=0),
        subject_payload(color="roxo"),
        subject_payload(start_date="2026-12-01", end_date="2026-08-01"),
    ]

    for payload in invalid_payloads:
        response = client.post("/api/subjects", json=payload)
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "validation_error"


def test_user_cannot_read_update_or_delete_another_users_subject(
    client, user_factory, db_session
):
    owner = user_factory(email="dona@example.com")
    intruder = user_factory(email="ana@example.com")
    foreign_subject = Subject(
        user_id=owner.id,
        name="Banco de Dados",
        professor="Prof. Carlos",
        workload_hours=60,
        color="#E67E22",
    )
    db_session.add(foreign_subject)
    db_session.commit()
    db_session.refresh(foreign_subject)
    login(client, email=intruder.email)

    assert client.get(f"/api/subjects/{foreign_subject.id}").status_code == 404
    assert client.put(
        f"/api/subjects/{foreign_subject.id}", json=subject_payload()
    ).status_code == 404
    assert client.delete(f"/api/subjects/{foreign_subject.id}").status_code == 404
    assert client.get("/api/subjects").json() == []


def test_deleting_subject_cascades_its_tasks(client, user_factory, db_session):
    user = user_factory(email="ana@example.com")
    subject = Subject(
        user_id=user.id,
        name="UX e Interfaces",
        workload_hours=40,
        color="#00796B",
    )
    db_session.add(subject)
    db_session.flush()
    task = AcademicTask(
        subject_id=subject.id,
        title="Entregar protótipo",
        due_date=date(2026, 9, 10),
    )
    db_session.add(task)
    db_session.commit()
    task_id = task.id
    login(client, email=user.email)

    assert client.delete(f"/api/subjects/{subject.id}").status_code == 204
    db_session.expire_all()

    assert db_session.scalar(
        select(AcademicTask).where(AcademicTask.id == task_id)
    ) is None

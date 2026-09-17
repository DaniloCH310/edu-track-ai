def authenticate(client):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Ana Estudante",
            "email": "edu-ia@example.com",
            "password": "Senha-Forte-123",
        },
    )
    assert response.status_code == 201


def test_edu_ia_status_requires_session_and_hides_provider_configuration(client):
    assert client.get("/api/edu-ia").status_code == 401

    authenticate(client)
    response = client.get("/api/edu-ia")

    assert response.status_code == 200
    assert response.json() == {"available": False}


def test_student_creates_private_conversation_for_an_owned_subject(
    client, user_factory, db_session
):
    from app.models.subject import Subject

    owner = user_factory(email="owner-edu-ia@example.com")
    subject = Subject(
        user_id=owner.id,
        name="Python Aplicado",
        workload_hours=80,
        color="#6750A4",
    )
    db_session.add(subject)
    db_session.commit()
    authenticate_response = client.post(
        "/api/auth/login",
        json={"email": owner.email, "password": "Senha-Forte-123"},
    )
    assert authenticate_response.status_code == 200

    created = client.post("/api/edu-ia/conversations", json={"subject_id": str(subject.id)})

    assert created.status_code == 201
    payload = created.json()
    assert payload["title"] == "Python Aplicado"
    assert payload["subject_id"] == str(subject.id)
    assert payload["task_id"] is None
    listed = client.get("/api/edu-ia/conversations")
    assert [item["id"] for item in listed.json()] == [payload["id"]]


def test_student_cannot_create_conversation_for_another_students_subject(
    client, user_factory, db_session
):
    from app.models.subject import Subject

    owner = user_factory(email="owner-private@example.com")
    intruder = user_factory(email="intruder-private@example.com")
    subject = Subject(
        user_id=owner.id,
        name="Banco de Dados",
        workload_hours=60,
        color="#6750A4",
    )
    db_session.add(subject)
    db_session.commit()
    login = client.post(
        "/api/auth/login",
        json={"email": intruder.email, "password": "Senha-Forte-123"},
    )
    assert login.status_code == 200

    response = client.post("/api/edu-ia/conversations", json={"subject_id": str(subject.id)})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "subject_not_found"


class FakeEduAIClient:
    def __init__(self):
        self.instruction = ""
        self.messages = []

    def generate_reply(self, instruction, messages):
        self.instruction = instruction
        self.messages = messages
        return "Comece separando o problema em partes menores."


def test_edu_ia_saves_question_and_reply_with_task_context(
    client, user_factory, db_session, monkeypatch
):
    from datetime import date
    from types import SimpleNamespace

    import app.api.edu_ia as edu_ia_api
    from app.models.subject import Subject
    from app.models.task import AcademicTask

    user = user_factory(email="tutor-context@example.com")
    subject = Subject(
        user_id=user.id,
        name="Python Aplicado",
        description="Fundamentos de programação.",
        workload_hours=80,
        color="#6750A4",
    )
    db_session.add(subject)
    db_session.flush()
    task = AcademicTask(
        subject_id=subject.id,
        title="Lista de funções",
        description="Resolver exercícios sobre parâmetros e retorno.",
        due_date=date(2026, 9, 20),
    )
    db_session.add(task)
    db_session.commit()
    fake_client = FakeEduAIClient()
    monkeypatch.setattr(
        edu_ia_api,
        "get_settings",
        lambda: SimpleNamespace(
            edu_ai_enabled=True,
            gemini_api_key="test-key",
            gemini_model="gemini-2.5-flash",
            edu_ai_requests_per_minute=5,
            edu_ai_requests_per_day=50,
        ),
    )
    client.app.dependency_overrides[edu_ia_api.get_edu_ai_client] = lambda: fake_client
    login = client.post(
        "/api/auth/login",
        json={"email": user.email, "password": "Senha-Forte-123"},
    )
    assert login.status_code == 200
    conversation = client.post(
        "/api/edu-ia/conversations", json={"task_id": str(task.id)}
    ).json()

    response = client.post(
        f"/api/edu-ia/conversations/{conversation['id']}/messages",
        json={"content": "Como posso começar?"},
    )

    assert response.status_code == 201
    assert response.json()["role"] == "assistant"
    assert "Python Aplicado" in fake_client.instruction
    assert "Lista de funções" in fake_client.instruction
    assert fake_client.messages[-1] == {"role": "user", "content": "Como posso começar?"}
    detail = client.get(f"/api/edu-ia/conversations/{conversation['id']}").json()
    assert [message["role"] for message in detail["messages"]] == ["user", "assistant"]

    deleted = client.delete(f"/api/edu-ia/conversations/{conversation['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/api/edu-ia/conversations/{conversation['id']}").status_code == 404
    assert client.get("/api/edu-ia/conversations").json() == []

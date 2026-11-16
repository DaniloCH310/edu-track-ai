from datetime import UTC, date, datetime
from io import BytesIO

import pytest
from pypdf import PdfReader

from app.models.subject import Subject
from app.models.task import AcademicTask, TaskStatus


def pdf_text(response):
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["cache-control"] == "no-store"
    assert response.content.startswith(b"%PDF-")
    return "\n".join(page.extract_text() for page in PdfReader(BytesIO(response.content)).pages)


def login(client, user):
    assert (
        client.post(
            "/api/auth/login",
            json={
                "email": user.email,
                "password": "Senha-Forte-123",
            },
        ).status_code
        == 200
    )


def test_report_requires_login(client):
    assert client.get("/api/reports/generate").status_code == 401


def test_weekly_report_is_private_and_distinguishes_deadlines_from_completions(
    client,
    user_factory,
    db_session,
):
    user = user_factory()
    other = user_factory(email="other@example.com")
    own = Subject(user_id=user.id, name="Funções & <Python>", workload_hours=60)
    foreign = Subject(user_id=other.id, name="SEGREDO DISCIPLINA", workload_hours=60)
    db_session.add_all([own, foreign])
    db_session.flush()
    db_session.add_all(
        [
            AcademicTask(subject_id=own.id, title="Prazo da semana", due_date=date(2026, 11, 16)),
            AcademicTask(
                subject_id=own.id,
                title="Concluída fora do prazo",
                due_date=date(2026, 11, 10),
                status=TaskStatus.COMPLETED,
                completed_at=datetime(2026, 11, 17, 12, tzinfo=UTC),
            ),
            # Monday UTC, but still Sunday in Sao Paulo: outside the report.
            AcademicTask(
                subject_id=own.id,
                title="Conclusão da semana anterior",
                due_date=date(2026, 11, 1),
                status=TaskStatus.COMPLETED,
                completed_at=datetime(2026, 11, 16, 1, tzinfo=UTC),
            ),
            AcademicTask(
                subject_id=foreign.id, title="SEGREDO TAREFA", due_date=date(2026, 11, 16)
            ),
        ]
    )
    db_session.commit()
    login(client, user)
    response = client.get("/api/reports/generate?week_start=2026-11-18")
    text = pdf_text(response)
    assert "2026-11-16" in response.headers["content-disposition"]
    assert "16/11/2026 a 22/11/2026" in text
    assert "0 de 1 tarefas com prazo nesta semana" in text
    assert "1 conclusões registradas no período" in text
    assert "Concluída fora do prazo" in text
    assert "Conclusão da semana anterior" not in text
    assert "Funções & <Python>" in text
    assert "67%" in text
    assert "SEGREDO" not in text


def test_empty_report_and_invalid_inputs(client, user_factory):
    login(client, user_factory())
    text = pdf_text(client.get("/api/reports/generate?week_start=2026-11-16"))
    assert "0 de 0 tarefas" in text
    assert "Nenhuma disciplina cadastrada" in text
    for query in ("week_start=bad", "timezone=Invalid/Zone", "week_start=9999-12-31"):
        assert client.get(f"/api/reports/generate?{query}").status_code == 422


@pytest.mark.parametrize("count", [100])
def test_report_paginates_long_untrusted_titles(client, user_factory, db_session, count):
    user = user_factory()
    subject = Subject(user_id=user.id, name=("Disciplina longa " * 10)[:160], workload_hours=60)
    db_session.add(subject)
    db_session.flush()
    for index in range(count):
        db_session.add(
            AcademicTask(
                subject_id=subject.id,
                title=f"Item {index:03} <b>literal</b> & " + "X" * 140,
                due_date=date(2026, 11, 16),
            )
        )
    db_session.commit()
    login(client, user)
    response = client.get("/api/reports/generate?week_start=2026-11-16")
    text = pdf_text(response)
    assert "Item 000 <b>literal</b> &" in text
    assert "Item 099 <b>literal</b> &" in text
    assert len(PdfReader(BytesIO(response.content)).pages) > 1

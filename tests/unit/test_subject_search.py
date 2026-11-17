"""HTTP/repository tests in disposable SQLite memory, never the configured database."""

from datetime import UTC, date, datetime, timedelta
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base, engine, get_db
from app.core.security import create_access_token
from app.main import create_app
from app.models.subject import Subject
from app.models.task import AcademicTask, TaskStatus
from app.models.user import User
from app.repositories import subjects as repository


@pytest.fixture
def search_case(monkeypatch):
    # An accidental fallback to the configured PostgreSQL engine fails before I/O.
    monkeypatch.setattr(engine, "connect", Mock(side_effect=AssertionError("No PostgreSQL")))
    memory = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        execution_options={"schema_translate_map": {"private": None}},
    )
    Base.metadata.create_all(memory)
    with Session(memory) as db:
        users = [
            User(name=f"Student {i}", email=f"s{i}@example.com", password_hash="unused")
            for i in range(2)
        ]
        db.add_all(users)
        db.flush()
        names = [
            "Python Basics",
            "Python Advanced",
            "Completed",
            "Today",
            "Future",
            "Empty",
            "100%_Lab",
            "Python Foreign",
        ]
        subjects = [
            Subject(name=name, user_id=users[int(i == 7)].id, workload_hours=30)
            for i, name in enumerate(names)
        ]
        db.add_all(subjects)
        db.flush()
        # At this instant UTC is Nov 18, but Sao Paulo is still Nov 17.
        instant = datetime(2026, 11, 18, 1, 30, tzinfo=UTC)
        clock = Mock()
        clock.now.side_effect = lambda zone: instant.astimezone(zone)
        monkeypatch.setattr(repository, "datetime", clock)
        today = date(2026, 11, 17)
        for index, offset, status in [
            (0, -1, TaskStatus.PENDING),
            (1, -2, TaskStatus.PENDING),
            (1, -1, TaskStatus.IN_PROGRESS),
            (2, -1, TaskStatus.COMPLETED),
            (3, 0, TaskStatus.PENDING),
            (4, 1, TaskStatus.PENDING),
            (7, -1, TaskStatus.PENDING),
        ]:
            db.add(
                AcademicTask(
                    subject_id=subjects[index].id,
                    title="Test task",
                    due_date=today + timedelta(days=offset),
                    status=status,
                )
            )
        db.commit()
        application = create_app()
        application.dependency_overrides[get_db] = lambda: db
        with TestClient(application) as http:
            http.cookies.set("edutrack_session", create_access_token(users[0].id))
            yield http, users
    memory.dispose()


def names(http, params=None):
    response = http.get("/api/subjects", params=params or {})
    assert response.status_code == 200
    return [item["name"] for item in response.json()]


@pytest.mark.parametrize(
    "query,expected",
    [
        ("Basics", ["Python Basics"]),
        ("missing", []),
        ("  pYtHoN  ", ["Python Advanced", "Python Basics"]),
        ("%_", ["100%_Lab"]),
        ("' OR 1=1 --", []),
    ],
)
def test_literal_name_search(search_case, query, expected):
    assert names(search_case[0], {"query": query}) == expected


def test_overdue_excludes_today_completed_future_empty_and_other_user(search_case):
    # Includes one pending and multiple pending/in-progress tasks without duplicates.
    assert names(search_case[0], {"overdue": "true"}) == ["Python Advanced", "Python Basics"]


@pytest.mark.parametrize(
    "query,expected",
    [
        ("Basics", ["Python Basics"]),
        ("Today", []),
        ("Foreign", []),
    ],
)
def test_filters_combine_with_and(search_case, query, expected):
    assert names(search_case[0], {"query": query, "overdue": "true"}) == expected


def test_unfiltered_compatibility_and_blank_name(search_case):
    http, _ = search_case
    expected = [
        "100%_Lab",
        "Completed",
        "Empty",
        "Future",
        "Python Advanced",
        "Python Basics",
        "Today",
    ]
    assert names(http) == expected
    assert names(http, {"query": "   ", "overdue": "false"}) == expected
    assert names(http, {"query": ""}) == expected
    assert "source" in http.get("/api/subjects").json()[0]


def test_owner_is_derived_from_session(search_case):
    http, users = search_case
    http.cookies.set("edutrack_session", create_access_token(users[1].id))
    assert names(http) == ["Python Foreign"]
    assert names(http, {"query": "python", "overdue": "true"}) == ["Python Foreign"]
    http.cookies.clear()
    assert http.get("/api/subjects?overdue=true").status_code == 401


@pytest.mark.parametrize("params", [{"query": "x" * 161}, {"overdue": "invalid"}])
def test_invalid_filters_are_rejected(search_case, params):
    assert search_case[0].get("/api/subjects", params=params).status_code == 422


def test_postgresql_compilation_uses_bound_values_and_exists():
    db = Mock()
    db.scalars.return_value = []
    repository.SubjectRepository.list_for_user(db, User().id, query="%_test", overdue=True)
    statement = db.scalars.call_args.args[0]
    compiled = statement.compile(dialect=postgresql.dialect())
    assert "EXISTS" in str(compiled)
    assert "ILIKE" in str(compiled)
    assert "%_test" not in str(compiled)
    assert "/%/_test" in compiled.params.values()


def test_swagger_declares_optional_filters(search_case):
    schema = search_case[0].get("/openapi.json").json()
    parameters = schema["paths"]["/api/subjects"]["get"]["parameters"]
    filters = {p["name"]: p for p in parameters if p["in"] == "query"}
    assert set(filters) == {"query", "overdue"}
    assert not any(p["required"] for p in filters.values())

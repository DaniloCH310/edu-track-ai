import os

import pytest
from fastapi.testclient import TestClient

from app.core.database_safety import clean_test_database, configure_test_environment

configure_test_environment(os.environ)
os.environ.setdefault("JWT_SECRET", "test-secret-with-at-least-thirty-two-characters")
os.environ.setdefault("SMTP_USERNAME", "tests@example.com")
os.environ.setdefault("SMTP_PASSWORD", "not-a-real-password")
os.environ.setdefault("SMTP_FROM_EMAIL", "tests@example.com")
os.environ["GOOGLE_CLASSROOM_ENABLED"] = "false"
os.environ["EDU_AI_ENABLED"] = "false"


@pytest.fixture(autouse=True)
def isolated_request_budget(monkeypatch):
    from app.services import request_budget

    budget = request_budget.RequestBudget()
    monkeypatch.setattr(request_budget, "get_request_budget", lambda: budget)


@pytest.fixture
def database_cleaner():
    from app.core.config import get_settings
    from app.core.database import engine

    def truncate() -> None:
        clean_test_database(
            engine,
            environment=get_settings().environment,
            github_actions=os.environ.get("GITHUB_ACTIONS") == "true",
        )

    truncate()
    try:
        yield
    finally:
        truncate()


@pytest.fixture
def db_session(database_cleaner):
    from app.core.database import SessionLocal

    with SessionLocal() as session:
        yield session


@pytest.fixture
def user_factory(db_session):
    from app.core.security import hash_password
    from app.models.user import User

    def create_user(
        *,
        name: str = "Ana Estudante",
        email: str = "ana@example.com",
        password: str = "Senha-Forte-123",
        is_active: bool = True,
    ) -> User:
        user = User(
            name=name,
            email=email.strip().lower(),
            password_hash=hash_password(password),
            is_active=is_active,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return create_user


@pytest.fixture
def client(database_cleaner):
    from app.main import create_app

    with TestClient(create_app()) as test_client:
        yield test_client

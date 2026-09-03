import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://edutrack:edutrack_test@127.0.0.1:54330/edutrack_test",
)
os.environ.setdefault("JWT_SECRET", "test-secret-with-at-least-thirty-two-characters")
os.environ.setdefault("SMTP_USERNAME", "tests@example.com")
os.environ.setdefault("SMTP_PASSWORD", "not-a-real-password")
os.environ.setdefault("SMTP_FROM_EMAIL", "tests@example.com")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text


@pytest.fixture
def database_cleaner():
    from app.core.database import engine

    def truncate() -> None:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "TRUNCATE TABLE private.classroom_task_links, "
                    "private.classroom_course_links, private.classroom_connections, "
                    "password_reset_tokens, academic_tasks, subjects, users "
                    "RESTART IDENTITY CASCADE"
                )
            )

    truncate()
    yield
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

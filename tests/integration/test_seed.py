from sqlalchemy import func, select

from app.models.subject import Subject
from app.models.task import AcademicTask
from app.models.user import User
from scripts.seed import seed_demo


def test_demo_seed_is_idempotent(db_session):
    first = seed_demo(db_session, "demo@example.com", "Demo-Segura-123")
    second = seed_demo(db_session, "demo@example.com", "Demo-Segura-123")

    assert first.id == second.id
    assert db_session.scalar(
        select(func.count()).select_from(User).where(User.email == "demo@example.com")
    ) == 1
    assert db_session.scalar(
        select(func.count()).select_from(Subject).where(Subject.user_id == first.id)
    ) == 3
    assert db_session.scalar(
        select(func.count())
        .select_from(AcademicTask)
        .join(Subject)
        .where(Subject.user_id == first.id)
    ) == 5

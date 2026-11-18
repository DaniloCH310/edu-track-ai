"""Repository tests in disposable SQLite memory only; never use DATABASE_URL."""

from copy import deepcopy
from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session

from app.api.errors import ApiError
from app.api.tasks import update_task
from app.models.review_mission import ReviewMission, ReviewMissionStatus
from app.models.subject import Subject
from app.models.task import AcademicTask, TaskStatus
from app.models.user import User
from app.repositories.review_missions import ReviewMissionRepository, review_due_date
from app.repositories.subjects import SubjectRepository
from app.repositories.tasks import TaskRepository
from app.schemas.task import TaskUpdate
from app.services.review_missions import create_questions, is_available


@pytest.fixture
def memory_session():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    # Only portable tables needed here; no app engine, PostgreSQL or external services.
    tables = [model.__table__ for model in (User, Subject, AcademicTask, ReviewMission)]
    User.metadata.create_all(engine, tables=tables)
    with Session(engine, autoflush=False, expire_on_commit=False) as db:
        yield db
    engine.dispose()


@pytest.fixture
def scenario(memory_session):
    db = memory_session
    owner = User(name="Student", email="student@example.com", password_hash="unused")
    other = User(name="Other", email="other@example.com", password_hash="unused")
    db.add_all([owner, other])
    db.flush()
    old = Subject(user_id=owner.id, name="Original subject", workload_hours=30)
    new = Subject(user_id=owner.id, name="New subject", workload_hours=30)
    foreign = Subject(user_id=other.id, name="Private subject", workload_hours=30)
    db.add_all([old, new, foreign])
    db.flush()
    task = AcademicTask(
        subject_id=old.id,
        title="Review concepts",
        due_date=date(2026, 1, 1),
        status=TaskStatus.COMPLETED,
        completed_at=datetime(2026, 1, 1, 12, tzinfo=UTC),
    )
    db.add(task)
    db.flush()
    ReviewMissionRepository.sync_for_task(db, task)
    db.commit()
    mission = db.scalar(select(ReviewMission))
    return SimpleNamespace(
        db=db,
        owner=owner,
        other=other,
        old=old,
        new=new,
        foreign=foreign,
        task=task,
        mission=mission,
    )


def payload(task, subject):
    return TaskUpdate(
        subject_id=subject.id, title=task.title, due_date=task.due_date, status=task.status
    )


def history(mission):
    return deepcopy(
        {
            name: getattr(mission, name)
            for name in (
                "id",
                "task_id",
                "due_date",
                "status",
                "questions",
                "answers",
                "mastery_percent",
                "mastery_summary",
                "completed_at",
                "created_at",
            )
        }
    )


def test_initial_review_is_unique_and_scheduled_for_original_subject(scenario):
    s = scenario
    assert s.mission.subject_id == s.old.id
    assert s.mission.due_date == review_due_date(s.task.completed_at)
    assert s.mission.status == ReviewMissionStatus.PENDING
    assert not s.mission.questions
    assert not is_available(s.mission, date(2026, 1, 1))
    before = history(s.mission)
    for _ in range(3):
        ReviewMissionRepository.sync_for_task(s.db, s.task)
        s.db.commit()
    assert history(s.mission) == before
    assert s.db.scalar(select(func.count()).select_from(ReviewMission)) == 1


@pytest.mark.parametrize("status", list(ReviewMissionStatus))
def test_transfer_preserves_mission_history_and_is_idempotent(scenario, status):
    s = scenario
    s.mission.status = status
    if status != ReviewMissionStatus.PENDING:
        s.mission.questions = ["Concept in Original subject?", "Example?", "Application?"]
        s.mission.answers = ["Existing answer", "Example", "Application"]
    if status == ReviewMissionStatus.COMPLETED:
        s.mission.mastery_percent = 90
        s.mission.mastery_summary = "Understands the original concepts"
        s.mission.completed_at = datetime(2026, 1, 5, 12, tzinfo=UTC)
    s.db.commit()
    s.db.refresh(s.mission)
    before = history(s.mission)
    task_completion = s.task.completed_at
    TaskRepository.update(s.db, s.task, payload(s.task, s.new))
    assert s.mission.subject_id == s.task.subject_id == s.new.id
    assert s.task.completed_at.replace(tzinfo=UTC) == task_completion
    assert history(s.mission) == before
    for _ in range(3):
        ReviewMissionRepository.sync_for_task(s.db, s.task)
        s.db.commit()
    assert history(s.mission) == before
    assert s.db.scalar(select(func.count()).select_from(ReviewMission)) == 1

    # Deleting the previous subject must not cascade into the transferred history.
    SubjectRepository.delete(s.db, s.old)
    s.db.expire_all()
    assert s.db.get(AcademicTask, s.task.id) is not None
    retained = s.db.get(ReviewMission, before["id"])
    assert retained is not None
    assert history(retained) == before
    if status == ReviewMissionStatus.PENDING:
        create_questions(retained, s.task, s.new, None)
        assert "New subject" in retained.questions[1]
    elif status == ReviewMissionStatus.IN_PROGRESS:
        ai = Mock()
        create_questions(retained, s.task, s.new, ai)
        ai.generate_reply.assert_not_called()
        assert retained.questions == before["questions"]


@pytest.mark.parametrize("delete_target", ["task", "subject"])
def test_deleting_current_parent_cascades_review(scenario, delete_target):
    s = scenario
    TaskRepository.update(s.db, s.task, payload(s.task, s.new))
    if delete_target == "task":
        TaskRepository.delete(s.db, s.task)
    else:
        SubjectRepository.delete(s.db, s.new)
    assert s.db.scalar(select(func.count()).select_from(ReviewMission)) == 0
    assert s.db.scalar(select(func.count()).select_from(AcademicTask)) == 0


def test_transferred_review_remains_private(scenario):
    s = scenario
    TaskRepository.update(s.db, s.task, payload(s.task, s.new))
    assert len(ReviewMissionRepository.list_for_user(s.db, s.owner.id)) == 1
    assert ReviewMissionRepository.get_for_user(s.db, s.mission.id, s.owner.id)
    assert ReviewMissionRepository.list_for_user(s.db, s.other.id) == []
    assert ReviewMissionRepository.get_for_user(s.db, s.mission.id, s.other.id) is None


def test_inconsistent_legacy_link_does_not_expose_another_users_task(scenario):
    s = scenario
    s.mission.subject_id = s.foreign.id
    s.db.commit()
    assert ReviewMissionRepository.list_for_user(s.db, s.other.id) == []
    assert ReviewMissionRepository.get_for_user(s.db, s.mission.id, s.other.id) is None


def test_api_rejects_transfer_to_unowned_subject(monkeypatch):
    user = SimpleNamespace(id=uuid4())
    task = SimpleNamespace(id=uuid4())
    db = Mock()
    get_task = Mock(return_value=task)
    get_subject = Mock(return_value=None)
    update = Mock()
    monkeypatch.setattr(TaskRepository, "get_for_user", get_task)
    monkeypatch.setattr(SubjectRepository, "get_for_user", get_subject)
    monkeypatch.setattr(TaskRepository, "update", update)
    data = TaskUpdate(subject_id=uuid4(), title="Task", due_date=date.today())
    with pytest.raises(ApiError) as caught:
        update_task(task.id, data, user, db)
    assert caught.value.status_code == 404
    get_task.assert_called_once_with(db, task.id, user.id)
    get_subject.assert_called_once_with(db, data.subject_id, user.id)
    update.assert_not_called()
    db.commit.assert_not_called()


def test_sync_changes_roll_back_with_task(scenario):
    s = scenario
    task_id, mission_id = s.task.id, s.mission.id
    s.task.subject_id = s.new.id
    ReviewMissionRepository.sync_for_task(s.db, s.task)
    s.db.flush()
    s.db.rollback()
    assert s.db.get(AcademicTask, task_id).subject_id == s.old.id
    assert s.db.get(ReviewMission, mission_id).subject_id == s.old.id


def test_repeated_sync_before_first_commit_does_not_duplicate(scenario):
    s = scenario
    task = AcademicTask(
        subject_id=s.new.id,
        title="Another task",
        due_date=date(2026, 1, 1),
        status=TaskStatus.COMPLETED,
        completed_at=datetime(2026, 1, 1, 12, tzinfo=UTC),
    )
    s.db.add(task)
    s.db.flush()
    for _ in range(3):
        ReviewMissionRepository.sync_for_task(s.db, task)
    s.db.commit()
    assert (
        s.db.scalar(
            select(func.count()).select_from(ReviewMission).where(ReviewMission.task_id == task.id)
        )
        == 1
    )


@pytest.mark.parametrize("status", list(ReviewMissionStatus))
def test_reopening_preserves_completed_history_only(scenario, status):
    s = scenario
    s.mission.status = status
    s.db.commit()
    data = payload(s.task, s.new).model_copy(update={"status": TaskStatus.IN_PROGRESS})
    TaskRepository.update(s.db, s.task, data)
    if status == ReviewMissionStatus.COMPLETED:
        assert s.mission.subject_id == s.new.id
        assert s.mission.status == status
    else:
        assert s.db.scalar(select(func.count()).select_from(ReviewMission)) == 0

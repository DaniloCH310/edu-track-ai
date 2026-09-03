import base64
from uuid import UUID

import pytest
from sqlalchemy import func, select

from app.integrations.google_classroom.crypto import encrypt_refresh_token
from app.integrations.google_classroom.sync import (
    ClassroomSyncService,
    map_submission_status,
)
from app.models.subject import Subject
from app.models.task import AcademicTask, TaskStatus
from app.repositories.classroom import ClassroomRepository

USER_ID = UUID("11111111-1111-4111-8111-111111111111")
KEY = base64.urlsafe_b64encode(b"s" * 32).decode()


class FakeClassroomGateway:
    task_title = "Projeto final"
    task_day = 15
    submission_state = "CREATED"

    def refresh_access_token(self, refresh_token: str) -> str:
        assert refresh_token == "fake-refresh-secret"
        return "memory-only-access"

    def list_active_courses(self, access_token: str) -> list[dict]:
        assert access_token == "memory-only-access"
        return [
            {"id": "course-1", "name": "Python Aplicado", "courseState": "ACTIVE"}
        ]

    def list_published_coursework(self, access_token: str, course_id: str) -> list[dict]:
        assert course_id == "course-1"
        return [
            {
                "id": "work-1",
                "title": self.task_title,
                "description": "Entregar analise",
                "dueDate": {"year": 2026, "month": 9, "day": self.task_day},
                "alternateLink": "https://classroom.google.com/c/example",
                "updateTime": "2026-09-03T12:00:00Z",
            },
            {"id": "work-no-date", "title": "Leitura livre"},
        ]

    def list_my_submissions(
        self, access_token: str, course_id: str, coursework_id: str
    ) -> list[dict]:
        return [{"id": "submission-1", "state": self.submission_state}]


@pytest.fixture
def configured_connection(db_session, user_factory):
    user = user_factory(email="classroom-sync@example.com")
    ClassroomRepository.upsert_connection(
        db_session,
        user.id,
        encrypt_refresh_token("fake-refresh-secret", KEY),
        "scope-a scope-b",
    )
    db_session.commit()
    return user


@pytest.mark.parametrize(
    ("remote", "local", "expected"),
    [
        ("TURNED_IN", TaskStatus.PENDING, TaskStatus.COMPLETED),
        ("RETURNED", TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED),
        ("RECLAIMED", TaskStatus.COMPLETED, TaskStatus.PENDING),
        ("CREATED", TaskStatus.IN_PROGRESS, TaskStatus.IN_PROGRESS),
        ("NEW", TaskStatus.PENDING, TaskStatus.PENDING),
        (None, TaskStatus.IN_PROGRESS, TaskStatus.IN_PROGRESS),
    ],
)
def test_submission_state_mapping(remote, local, expected):
    assert map_submission_status(remote, local) == expected


def test_repeated_sync_creates_records_only_once(configured_connection, db_session):
    service = ClassroomSyncService()

    first = service.sync(db_session, configured_connection.id, FakeClassroomGateway(), KEY)
    second = service.sync(db_session, configured_connection.id, FakeClassroomGateway(), KEY)

    assert first.model_dump() == {
        "courses_created": 1,
        "courses_updated": 0,
        "tasks_created": 1,
        "tasks_updated": 0,
        "skipped_without_due_date": 1,
        "warnings": [],
    }
    assert second.courses_created == 0
    assert second.tasks_created == 0
    assert db_session.scalar(select(func.count(Subject.id))) == 1
    assert db_session.scalar(select(func.count(AcademicTask.id))) == 1


def test_sync_updates_remote_fields_and_completion(configured_connection, db_session):
    service = ClassroomSyncService()
    service.sync(db_session, configured_connection.id, FakeClassroomGateway(), KEY)
    changed = FakeClassroomGateway()
    changed.task_title = "Projeto final revisado"
    changed.task_day = 20
    changed.submission_state = "TURNED_IN"

    result = service.sync(db_session, configured_connection.id, changed, KEY)
    task = db_session.scalar(select(AcademicTask))

    assert result.tasks_updated == 1
    assert task is not None
    assert task.title == "Projeto final revisado"
    assert task.due_date.isoformat() == "2026-09-20"
    assert task.status == TaskStatus.COMPLETED
    assert task.completed_at is not None


def test_failure_rolls_back_all_imported_records(configured_connection, db_session):
    class FailingGateway(FakeClassroomGateway):
        def list_active_courses(self, access_token: str) -> list[dict]:
            return [
                {"id": "course-1", "name": "Python", "courseState": "ACTIVE"},
                {"id": "course-2", "name": "Banco de dados", "courseState": "ACTIVE"},
            ]

        def list_published_coursework(
            self, access_token: str, course_id: str
        ) -> list[dict]:
            if course_id == "course-2":
                raise RuntimeError("simulated provider failure")
            return super().list_published_coursework(access_token, course_id)

    with pytest.raises(RuntimeError, match="simulated provider failure"):
        ClassroomSyncService().sync(
            db_session, configured_connection.id, FailingGateway(), KEY
        )

    assert db_session.scalar(select(func.count(Subject.id))) == 0
    assert db_session.scalar(select(func.count(AcademicTask.id))) == 0
    connection = ClassroomRepository.get_connection(db_session, configured_connection.id)
    assert connection is not None
    assert connection.last_error_code == "classroom_sync_failed"

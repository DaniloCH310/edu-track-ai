from datetime import date

from sqlalchemy import func, select

from app.models import AcademicTask, Subject, TaskStatus
from app.models.classroom import ClassroomConnection
from app.repositories.classroom import ClassroomRepository

SCOPES = (
    "https://www.googleapis.com/auth/classroom.courses.readonly "
    "https://www.googleapis.com/auth/classroom.coursework.me.readonly"
)


def test_repository_upserts_one_connection_for_each_user(db_session, user_factory):
    user = user_factory()

    first = ClassroomRepository.upsert_connection(
        db_session, user.id, "encrypted-one", SCOPES
    )
    second = ClassroomRepository.upsert_connection(
        db_session, user.id, "encrypted-two", SCOPES
    )
    db_session.commit()

    assert first.id == second.id
    assert second.encrypted_refresh_token == "encrypted-two"
    assert db_session.scalar(select(func.count(ClassroomConnection.id))) == 1


def test_repository_links_google_ids_to_safe_local_entities(db_session, user_factory):
    user = user_factory()
    connection = ClassroomRepository.upsert_connection(
        db_session, user.id, "encrypted", SCOPES
    )
    subject = Subject(user_id=user.id, name="Python", workload_hours=1)
    db_session.add(subject)
    db_session.flush()
    course_link = ClassroomRepository.create_course_link(
        db_session,
        connection.id,
        subject.id,
        classroom_course_id="course-1",
        course_state="ACTIVE",
    )
    task = AcademicTask(
        subject_id=subject.id,
        title="Projeto final",
        due_date=date(2026, 9, 15),
        status=TaskStatus.PENDING,
    )
    db_session.add(task)
    db_session.flush()
    task_link = ClassroomRepository.create_task_link(
        db_session,
        course_link.id,
        task.id,
        classroom_coursework_id="work-1",
        classroom_submission_id="submission-1",
        alternate_link="https://classroom.google.com/c/example",
        source_updated_at=None,
    )
    db_session.commit()
    db_session.refresh(subject)
    db_session.refresh(task)

    assert ClassroomRepository.get_course_link(
        db_session, connection.id, "course-1"
    ).id == course_link.id
    assert ClassroomRepository.get_task_link(
        db_session, course_link.id, "work-1"
    ).id == task_link.id
    assert subject.source == "google_classroom"
    assert task.source == "google_classroom"
    assert task.external_url == "https://classroom.google.com/c/example"


def test_deleting_connection_keeps_imported_subject_and_task(db_session, user_factory):
    user = user_factory()
    connection = ClassroomRepository.upsert_connection(
        db_session, user.id, "encrypted", SCOPES
    )
    subject = Subject(user_id=user.id, name="Python", workload_hours=1)
    db_session.add(subject)
    db_session.flush()
    course_link = ClassroomRepository.create_course_link(
        db_session, connection.id, subject.id, "course-1", "ACTIVE"
    )
    task = AcademicTask(
        subject_id=subject.id,
        title="Projeto final",
        due_date=date(2026, 9, 15),
    )
    db_session.add(task)
    db_session.flush()
    ClassroomRepository.create_task_link(
        db_session,
        course_link.id,
        task.id,
        "work-1",
        None,
        "https://classroom.google.com/c/example",
        None,
    )
    db_session.commit()

    ClassroomRepository.delete_connection(db_session, connection)
    db_session.commit()

    assert db_session.get(Subject, subject.id) is not None
    assert db_session.get(AcademicTask, task.id) is not None

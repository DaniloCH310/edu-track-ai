from datetime import UTC, date, datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy.orm import Session

from app.integrations.google_classroom.client import GoogleClassroomError
from app.integrations.google_classroom.crypto import decrypt_refresh_token
from app.models.base import utc_now
from app.models.subject import Subject
from app.models.task import AcademicTask, TaskStatus
from app.repositories.classroom import ClassroomRepository
from app.schemas.classroom import ClassroomSyncResult


class ClassroomGateway(Protocol):
    def refresh_access_token(self, refresh_token: str) -> str: ...

    def list_active_courses(self, access_token: str) -> list[dict]: ...

    def list_published_coursework(
        self, access_token: str, course_id: str
    ) -> list[dict]: ...

    def list_my_submissions(
        self, access_token: str, course_id: str, coursework_id: str
    ) -> list[dict]: ...


def map_submission_status(
    remote_state: str | None, local_status: TaskStatus
) -> TaskStatus:
    if remote_state in {"TURNED_IN", "RETURNED"}:
        return TaskStatus.COMPLETED
    if remote_state == "RECLAIMED":
        return TaskStatus.PENDING
    return local_status


class ClassroomSyncService:
    def sync(
        self,
        db: Session,
        user_id: UUID,
        client: ClassroomGateway,
        encryption_key: str,
    ) -> ClassroomSyncResult:
        result = ClassroomSyncResult()
        try:
            connection = ClassroomRepository.get_connection(db, user_id)
            if connection is None:
                raise ValueError("classroom_not_connected")

            refresh_token = decrypt_refresh_token(
                connection.encrypted_refresh_token, encryption_key
            )
            access_token = client.refresh_access_token(refresh_token)
            for remote_course in client.list_active_courses(access_token):
                self._sync_course(
                    db, connection.id, user_id, client, access_token, remote_course, result
                )

            connection.last_synced_at = utc_now()
            connection.last_error_code = None
            db.commit()
            return result
        except Exception as exception:
            db.rollback()
            connection = ClassroomRepository.get_connection(db, user_id)
            if connection is not None:
                connection.last_error_code = (
                    exception.code
                    if isinstance(exception, GoogleClassroomError)
                    else "classroom_sync_failed"
                )
                db.commit()
            raise

    def _sync_course(
        self,
        db: Session,
        connection_id: UUID,
        user_id: UUID,
        client: ClassroomGateway,
        access_token: str,
        remote: dict,
        result: ClassroomSyncResult,
    ) -> None:
        course_id = str(remote["id"])
        course_link = ClassroomRepository.get_course_link(db, connection_id, course_id)
        if course_link is None:
            subject = Subject(
                user_id=user_id,
                name=str(remote.get("name") or "Disciplina do Google Classroom")[:160],
                description=self._course_description(remote),
                workload_hours=1,
            )
            db.add(subject)
            db.flush()
            course_link = ClassroomRepository.create_course_link(
                db,
                connection_id,
                subject.id,
                course_id,
                str(remote.get("courseState") or "ACTIVE"),
            )
            result.courses_created += 1
        else:
            course_link.subject.name = str(
                remote.get("name") or course_link.subject.name
            )[:160]
            course_link.subject.description = self._course_description(remote)
            course_link.course_state = str(remote.get("courseState") or "ACTIVE")
            result.courses_updated += 1

        for coursework in client.list_published_coursework(access_token, course_id):
            if "dueDate" not in coursework:
                result.skipped_without_due_date += 1
                continue
            self._sync_coursework(
                db,
                course_link,
                client,
                access_token,
                course_id,
                coursework,
                result,
            )

    def _sync_coursework(
        self,
        db: Session,
        course_link,
        client: ClassroomGateway,
        access_token: str,
        course_id: str,
        remote: dict,
        result: ClassroomSyncResult,
    ) -> None:
        work_id = str(remote["id"])
        due_date = self._due_date(remote["dueDate"])
        submissions = client.list_my_submissions(access_token, course_id, work_id)
        submission = submissions[0] if submissions else {}
        task_link = ClassroomRepository.get_task_link(db, course_link.id, work_id)
        current_status = (
            task_link.task.status if task_link is not None else TaskStatus.PENDING
        )
        status = map_submission_status(submission.get("state"), current_status)

        if task_link is None:
            task = AcademicTask(
                subject_id=course_link.subject_id,
                title=str(remote.get("title") or "Atividade do Google Classroom")[:200],
                description=self._optional_text(remote.get("description")),
                due_date=due_date,
                status=status,
                completed_at=utc_now() if status == TaskStatus.COMPLETED else None,
            )
            db.add(task)
            db.flush()
            ClassroomRepository.create_task_link(
                db,
                course_link.id,
                task.id,
                work_id,
                self._optional_text(submission.get("id")),
                self._alternate_link(remote),
                self._remote_datetime(remote.get("updateTime")),
            )
            result.tasks_created += 1
            return

        task = task_link.task
        task.title = str(remote.get("title") or task.title)[:200]
        task.description = self._optional_text(remote.get("description"))
        task.due_date = due_date
        if status == TaskStatus.COMPLETED and task.status != TaskStatus.COMPLETED:
            task.completed_at = utc_now()
        elif status != TaskStatus.COMPLETED:
            task.completed_at = None
        task.status = status
        task_link.classroom_submission_id = self._optional_text(submission.get("id"))
        task_link.alternate_link = self._alternate_link(remote)
        task_link.source_updated_at = self._remote_datetime(remote.get("updateTime"))
        result.tasks_updated += 1

    @staticmethod
    def _course_description(remote: dict) -> str | None:
        return ClassroomSyncService._optional_text(
            remote.get("descriptionHeading") or remote.get("section")
        )

    @staticmethod
    def _optional_text(value: object) -> str | None:
        if not isinstance(value, str):
            return None
        stripped = value.strip()
        return stripped or None

    @staticmethod
    def _due_date(value: dict) -> date:
        return date(int(value["year"]), int(value["month"]), int(value["day"]))

    @staticmethod
    def _remote_datetime(value: object) -> datetime | None:
        if not isinstance(value, str):
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
        except ValueError:
            return None

    @staticmethod
    def _alternate_link(remote: dict) -> str:
        value = remote.get("alternateLink")
        if isinstance(value, str) and value.startswith("https://classroom.google.com/"):
            return value
        return "https://classroom.google.com/"

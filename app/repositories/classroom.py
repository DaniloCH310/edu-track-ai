from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.classroom import (
    ClassroomConnection,
    ClassroomCourseLink,
    ClassroomTaskLink,
)


class ClassroomRepository:
    @staticmethod
    def get_connection(db: Session, user_id: UUID) -> ClassroomConnection | None:
        return db.scalar(
            select(ClassroomConnection).where(ClassroomConnection.user_id == user_id)
        )

    @staticmethod
    def upsert_connection(
        db: Session,
        user_id: UUID,
        encrypted_refresh_token: str,
        granted_scopes: str,
    ) -> ClassroomConnection:
        connection = ClassroomRepository.get_connection(db, user_id)
        if connection is None:
            connection = ClassroomConnection(
                user_id=user_id,
                encrypted_refresh_token=encrypted_refresh_token,
                granted_scopes=granted_scopes,
            )
            db.add(connection)
        else:
            connection.encrypted_refresh_token = encrypted_refresh_token
            connection.granted_scopes = granted_scopes
            connection.last_error_code = None
        db.flush()
        return connection

    @staticmethod
    def get_course_link(
        db: Session, connection_id: UUID, classroom_course_id: str
    ) -> ClassroomCourseLink | None:
        return db.scalar(
            select(ClassroomCourseLink).where(
                ClassroomCourseLink.connection_id == connection_id,
                ClassroomCourseLink.classroom_course_id == classroom_course_id,
            )
        )

    @staticmethod
    def create_course_link(
        db: Session,
        connection_id: UUID,
        subject_id: UUID,
        classroom_course_id: str,
        course_state: str,
    ) -> ClassroomCourseLink:
        link = ClassroomCourseLink(
            connection_id=connection_id,
            subject_id=subject_id,
            classroom_course_id=classroom_course_id,
            course_state=course_state,
        )
        db.add(link)
        db.flush()
        return link

    @staticmethod
    def get_task_link(
        db: Session, course_link_id: UUID, classroom_coursework_id: str
    ) -> ClassroomTaskLink | None:
        return db.scalar(
            select(ClassroomTaskLink).where(
                ClassroomTaskLink.course_link_id == course_link_id,
                ClassroomTaskLink.classroom_coursework_id == classroom_coursework_id,
            )
        )

    @staticmethod
    def create_task_link(
        db: Session,
        course_link_id: UUID,
        task_id: UUID,
        classroom_coursework_id: str,
        classroom_submission_id: str | None,
        alternate_link: str,
        source_updated_at: datetime | None,
    ) -> ClassroomTaskLink:
        link = ClassroomTaskLink(
            course_link_id=course_link_id,
            task_id=task_id,
            classroom_coursework_id=classroom_coursework_id,
            classroom_submission_id=classroom_submission_id,
            alternate_link=alternate_link,
            source_updated_at=source_updated_at,
        )
        db.add(link)
        db.flush()
        return link

    @staticmethod
    def delete_connection(db: Session, connection: ClassroomConnection) -> None:
        db.delete(connection)
        db.flush()

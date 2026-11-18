from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.subject import Subject
from app.models.task import AcademicTask, TaskStatus
from app.schemas.subject import SubjectCreate, SubjectUpdate


class SubjectRepository:
    @staticmethod
    def list_for_user(
        db: Session, user_id: UUID, *, query: str | None = None, overdue: bool = False
    ) -> list[Subject]:
        statement = select(Subject).where(Subject.user_id == user_id)
        if query and query.strip():
            statement = statement.where(Subject.name.icontains(query.strip(), autoescape=True))
        if overdue:
            today = datetime.now(ZoneInfo("America/Sao_Paulo")).date()
            statement = statement.where(
                Subject.tasks.any(
                    (AcademicTask.due_date < today) & (AcademicTask.status != TaskStatus.COMPLETED)
                )
            )
        return list(
            db.scalars(
                statement.options(selectinload(Subject.classroom_link)).order_by(
                    func.lower(Subject.name), Subject.created_at
                )
            )
        )

    @staticmethod
    def get_for_user(db: Session, subject_id: UUID, user_id: UUID) -> Subject | None:
        return db.scalar(
            select(Subject)
            .where(Subject.id == subject_id, Subject.user_id == user_id)
            .options(selectinload(Subject.classroom_link))
        )

    @staticmethod
    def create(db: Session, user_id: UUID, data: SubjectCreate) -> Subject:
        subject = Subject(user_id=user_id, **data.model_dump())
        db.add(subject)
        db.commit()
        db.refresh(subject)
        return subject

    @staticmethod
    def update(db: Session, subject: Subject, data: SubjectUpdate) -> Subject:
        for field, value in data.model_dump().items():
            setattr(subject, field, value)
        db.commit()
        db.refresh(subject)
        return subject

    @staticmethod
    def delete(db: Session, subject: Subject) -> None:
        db.delete(subject)
        db.commit()

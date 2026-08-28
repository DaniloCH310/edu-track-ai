from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.subject import Subject
from app.schemas.subject import SubjectCreate, SubjectUpdate


class SubjectRepository:
    @staticmethod
    def list_for_user(db: Session, user_id: UUID) -> list[Subject]:
        return list(
            db.scalars(
                select(Subject)
                .where(Subject.user_id == user_id)
                .order_by(func.lower(Subject.name), Subject.created_at)
            )
        )

    @staticmethod
    def get_for_user(db: Session, subject_id: UUID, user_id: UUID) -> Subject | None:
        return db.scalar(
            select(Subject).where(
                Subject.id == subject_id, Subject.user_id == user_id
            )
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

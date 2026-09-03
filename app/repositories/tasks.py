from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.subject import Subject
from app.models.task import AcademicTask, TaskStatus
from app.schemas.task import TaskCreate, TaskOrder, TaskUpdate


class TaskRepository:
    @staticmethod
    def list_for_user(
        db: Session,
        user_id: UUID,
        *,
        query: str | None = None,
        status: TaskStatus | None = None,
        subject_id: UUID | None = None,
        order: TaskOrder = "due_asc",
    ) -> list[AcademicTask]:
        statement = (
            select(AcademicTask)
            .join(Subject)
            .where(Subject.user_id == user_id)
            .options(
                joinedload(AcademicTask.subject),
                joinedload(AcademicTask.classroom_link),
            )
        )
        if query and query.strip():
            pattern = f"%{query.strip()}%"
            statement = statement.where(
                or_(
                    AcademicTask.title.ilike(pattern),
                    func.coalesce(AcademicTask.description, "").ilike(pattern),
                )
            )
        if status is not None:
            statement = statement.where(AcademicTask.status == status)
        if subject_id is not None:
            statement = statement.where(AcademicTask.subject_id == subject_id)

        ordering = {
            "due_asc": (AcademicTask.due_date.asc(), AcademicTask.created_at.asc()),
            "due_desc": (AcademicTask.due_date.desc(), AcademicTask.created_at.desc()),
            "created_desc": (AcademicTask.created_at.desc(),),
        }
        return list(db.scalars(statement.order_by(*ordering[order])))

    @staticmethod
    def get_for_user(
        db: Session, task_id: UUID, user_id: UUID
    ) -> AcademicTask | None:
        return db.scalar(
            select(AcademicTask)
            .join(Subject)
            .where(AcademicTask.id == task_id, Subject.user_id == user_id)
            .options(
                joinedload(AcademicTask.subject),
                joinedload(AcademicTask.classroom_link),
            )
        )

    @staticmethod
    def create(db: Session, data: TaskCreate) -> AcademicTask:
        values = data.model_dump()
        values["completed_at"] = (
            datetime.now(UTC) if data.status == TaskStatus.COMPLETED else None
        )
        task = AcademicTask(**values)
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def update(db: Session, task: AcademicTask, data: TaskUpdate) -> AcademicTask:
        previous_status = task.status
        for field, value in data.model_dump().items():
            setattr(task, field, value)
        TaskRepository._set_completion_timestamp(task, previous_status)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def update_status(
        db: Session, task: AcademicTask, new_status: TaskStatus
    ) -> AcademicTask:
        previous_status = task.status
        task.status = new_status
        TaskRepository._set_completion_timestamp(task, previous_status)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def _set_completion_timestamp(
        task: AcademicTask, previous_status: TaskStatus
    ) -> None:
        if task.status == TaskStatus.COMPLETED and previous_status != TaskStatus.COMPLETED:
            task.completed_at = datetime.now(UTC)
        elif task.status != TaskStatus.COMPLETED:
            task.completed_at = None

    @staticmethod
    def delete(db: Session, task: AcademicTask) -> None:
        db.delete(task)
        db.commit()

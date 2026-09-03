from datetime import date, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.database import Base
from app.models.base import TimestampMixin


class TaskStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class AcademicTask(TimestampMixin, Base):
    __tablename__ = "academic_tasks"
    __table_args__ = (
        Index("ix_academic_tasks_subject_status", "subject_id", "status"),
        Index("ix_academic_tasks_due_date", "due_date"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    subject_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(
            TaskStatus,
            name="task_status",
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        nullable=False,
        default=TaskStatus.PENDING,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    subject: Mapped["Subject"] = relationship(back_populates="tasks")
    classroom_link: Mapped["ClassroomTaskLink | None"] = relationship(
        back_populates="task", passive_deletes=True, uselist=False
    )

    @property
    def subject_name(self) -> str:
        return self.subject.name

    @property
    def source(self) -> str:
        return "google_classroom" if self.classroom_link else "local"

    @property
    def external_url(self) -> str | None:
        return self.classroom_link.alternate_link if self.classroom_link else None


from app.models.classroom import ClassroomTaskLink  # noqa: E402
from app.models.subject import Subject  # noqa: E402

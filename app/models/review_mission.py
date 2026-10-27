from datetime import date, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, Uuid

from app.core.database import Base
from app.models.base import TimestampMixin


class ReviewMissionStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ReviewMission(TimestampMixin, Base):
    __tablename__ = "review_missions"
    __table_args__ = (
        Index("ix_review_missions_subject_due", "subject_id", "due_date"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    task_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("academic_tasks.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    subject_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
    )
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[ReviewMissionStatus] = mapped_column(
        Enum(
            ReviewMissionStatus,
            name="review_mission_status",
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        nullable=False,
        default=ReviewMissionStatus.PENDING,
    )
    questions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    answers: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    mastery_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mastery_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

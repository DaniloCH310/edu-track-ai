from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.database import Base
from app.models.base import TimestampMixin


class Subject(TimestampMixin, Base):
    __tablename__ = "subjects"
    __table_args__ = (
        CheckConstraint("workload_hours > 0", name="positive_workload"),
        CheckConstraint(
            "end_date IS NULL OR start_date IS NULL OR end_date >= start_date",
            name="valid_date_range",
        ),
        Index("ix_subjects_user_name", "user_id", "name"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    professor: Mapped[str | None] = mapped_column(String(160), nullable=True)
    workload_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    period: Mapped[str | None] = mapped_column(String(40), nullable=True)
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#6750A4")
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    user: Mapped["User"] = relationship(back_populates="subjects")
    tasks: Mapped[list["AcademicTask"]] = relationship(
        back_populates="subject", cascade="all, delete-orphan", passive_deletes=True
    )
    classroom_link: Mapped["ClassroomCourseLink | None"] = relationship(
        back_populates="subject", passive_deletes=True, uselist=False
    )

    @property
    def source(self) -> str:
        return "google_classroom" if self.classroom_link else "local"


from app.models.classroom import ClassroomCourseLink  # noqa: E402
from app.models.task import AcademicTask  # noqa: E402
from app.models.user import User  # noqa: E402

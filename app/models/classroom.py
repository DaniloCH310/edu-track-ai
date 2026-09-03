from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.database import Base
from app.models.base import TimestampMixin


class ClassroomConnection(TimestampMixin, Base):
    __tablename__ = "classroom_connections"
    __table_args__ = {"schema": "private"}

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    encrypted_refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    granted_scopes: Mapped[str] = mapped_column(Text, nullable=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)

    user: Mapped["User"] = relationship(back_populates="classroom_connection")
    course_links: Mapped[list["ClassroomCourseLink"]] = relationship(
        back_populates="connection", cascade="all, delete-orphan", passive_deletes=True
    )


class ClassroomCourseLink(TimestampMixin, Base):
    __tablename__ = "classroom_course_links"
    __table_args__ = (
        UniqueConstraint(
            "connection_id",
            "classroom_course_id",
            name="uq_classroom_course_links_connection_course",
        ),
        {"schema": "private"},
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    connection_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("private.classroom_connections.id", ondelete="CASCADE"),
        nullable=False,
    )
    subject_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    classroom_course_id: Mapped[str] = mapped_column(String(128), nullable=False)
    course_state: Mapped[str] = mapped_column(String(40), nullable=False)

    connection: Mapped[ClassroomConnection] = relationship(back_populates="course_links")
    subject: Mapped["Subject"] = relationship(back_populates="classroom_link")
    task_links: Mapped[list["ClassroomTaskLink"]] = relationship(
        back_populates="course_link", cascade="all, delete-orphan", passive_deletes=True
    )


class ClassroomTaskLink(TimestampMixin, Base):
    __tablename__ = "classroom_task_links"
    __table_args__ = (
        UniqueConstraint(
            "course_link_id",
            "classroom_coursework_id",
            name="uq_classroom_task_links_course_work",
        ),
        {"schema": "private"},
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    course_link_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("private.classroom_course_links.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("academic_tasks.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    classroom_coursework_id: Mapped[str] = mapped_column(String(128), nullable=False)
    classroom_submission_id: Mapped[str | None] = mapped_column(
        String(128), nullable=True
    )
    alternate_link: Mapped[str] = mapped_column(Text, nullable=False)
    source_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    course_link: Mapped[ClassroomCourseLink] = relationship(back_populates="task_links")
    task: Mapped["AcademicTask"] = relationship(back_populates="classroom_link")


from app.models.subject import Subject  # noqa: E402
from app.models.task import AcademicTask  # noqa: E402
from app.models.user import User  # noqa: E402

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.database import Base
from app.models.base import TimestampMixin, utc_now


class EduAIMessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class EduAIConversation(TimestampMixin, Base):
    __tablename__ = "edu_ai_conversations"
    __table_args__ = (Index("ix_edu_ai_conversations_user_updated", "user_id", "updated_at"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    subject_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True
    )
    task_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("academic_tasks.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)

    user: Mapped["User"] = relationship(back_populates="edu_ai_conversations")
    messages: Mapped[list["EduAIMessage"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", passive_deletes=True
    )


class EduAIMessage(Base):
    __tablename__ = "edu_ai_messages"
    __table_args__ = (
        Index("ix_edu_ai_messages_conversation_created", "conversation_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("edu_ai_conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[EduAIMessageRole] = mapped_column(
        Enum(
            EduAIMessageRole,
            name="edu_ai_message_role",
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    conversation: Mapped[EduAIConversation] = relationship(back_populates="messages")


from app.models.user import User  # noqa: E402

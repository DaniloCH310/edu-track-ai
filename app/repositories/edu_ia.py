from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.edu_ia import EduAIConversation, EduAIMessage, EduAIMessageRole


class EduAIRepository:
    @staticmethod
    def list_conversations(db: Session, user_id: UUID) -> list[EduAIConversation]:
        return list(
            db.scalars(
                select(EduAIConversation)
                .where(EduAIConversation.user_id == user_id)
                .order_by(EduAIConversation.updated_at.desc())
            )
        )

    @staticmethod
    def get_conversation(
        db: Session, conversation_id: UUID, user_id: UUID
    ) -> EduAIConversation | None:
        return db.scalar(
            select(EduAIConversation)
            .where(
                EduAIConversation.id == conversation_id,
                EduAIConversation.user_id == user_id,
            )
            .options(selectinload(EduAIConversation.messages))
        )

    @staticmethod
    def create_conversation(
        db: Session,
        user_id: UUID,
        title: str,
        subject_id: UUID | None,
        task_id: UUID | None,
    ) -> EduAIConversation:
        conversation = EduAIConversation(
            user_id=user_id,
            title=title,
            subject_id=subject_id,
            task_id=task_id,
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    @staticmethod
    def add_message(
        db: Session,
        conversation: EduAIConversation,
        role: EduAIMessageRole,
        content: str,
    ) -> EduAIMessage:
        message = EduAIMessage(conversation_id=conversation.id, role=role, content=content)
        conversation.updated_at = datetime.now(UTC)
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def list_messages(db: Session, conversation_id: UUID) -> list[EduAIMessage]:
        return list(
            db.scalars(
                select(EduAIMessage)
                .where(EduAIMessage.conversation_id == conversation_id)
                .order_by(EduAIMessage.created_at, EduAIMessage.id)
            )
        )

    @staticmethod
    def count_student_messages_since(db: Session, user_id: UUID, since: datetime) -> int:
        return int(
            db.scalar(
                select(func.count(EduAIMessage.id))
                .join(EduAIConversation)
                .where(
                    EduAIConversation.user_id == user_id,
                    EduAIMessage.role == EduAIMessageRole.USER,
                    EduAIMessage.created_at >= since,
                )
            )
            or 0
        )

    @staticmethod
    def delete_conversation(db: Session, conversation: EduAIConversation) -> None:
        db.delete(conversation)
        db.commit()

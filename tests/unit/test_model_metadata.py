from sqlalchemy import Enum

from app.core.database import Base
from app.models import (
    AcademicTask,
    ClassroomConnection,
    ClassroomCourseLink,
    ClassroomTaskLink,
    EduAIConversation,
    EduAIMessage,
    EduAIMessageRole,
    PasswordResetToken,
    Subject,
    TaskStatus,
    User,
)


def test_metadata_contains_the_approved_tables_and_columns():
    """Catches schema drift that removes required MVP persistence fields."""
    assert set(Base.metadata.tables) == {
        "users",
        "password_reset_tokens",
        "subjects",
        "academic_tasks",
        "edu_ai_conversations",
        "edu_ai_messages",
        "private.classroom_connections",
        "private.classroom_course_links",
        "private.classroom_task_links",
    }
    assert ClassroomConnection.__table__.schema == "private"
    assert ClassroomCourseLink.__table__.schema == "private"
    assert ClassroomTaskLink.__table__.schema == "private"
    assert set(User.__table__.columns.keys()) == {
        "id",
        "name",
        "email",
        "password_hash",
        "is_active",
        "created_at",
        "updated_at",
    }
    assert set(PasswordResetToken.__table__.columns.keys()) == {
        "id",
        "user_id",
        "token_hash",
        "expires_at",
        "used_at",
        "created_at",
    }
    assert set(Subject.__table__.columns.keys()) == {
        "id",
        "user_id",
        "name",
        "professor",
        "workload_hours",
        "description",
        "period",
        "color",
        "start_date",
        "end_date",
        "created_at",
        "updated_at",
    }
    assert set(AcademicTask.__table__.columns.keys()) == {
        "id",
        "subject_id",
        "title",
        "description",
        "due_date",
        "status",
        "completed_at",
        "created_at",
        "updated_at",
    }
    assert set(EduAIConversation.__table__.columns.keys()) == {
        "id",
        "user_id",
        "subject_id",
        "task_id",
        "title",
        "created_at",
        "updated_at",
    }
    assert set(EduAIMessage.__table__.columns.keys()) == {
        "id",
        "conversation_id",
        "role",
        "content",
        "created_at",
    }
    assert set(ClassroomConnection.__table__.columns.keys()) == {
        "id",
        "user_id",
        "encrypted_refresh_token",
        "granted_scopes",
        "last_synced_at",
        "last_error_code",
        "created_at",
        "updated_at",
    }
    assert set(ClassroomCourseLink.__table__.columns.keys()) == {
        "id",
        "connection_id",
        "subject_id",
        "classroom_course_id",
        "course_state",
        "created_at",
        "updated_at",
    }
    assert set(ClassroomTaskLink.__table__.columns.keys()) == {
        "id",
        "course_link_id",
        "task_id",
        "classroom_coursework_id",
        "classroom_submission_id",
        "alternate_link",
        "source_updated_at",
        "created_at",
        "updated_at",
    }


def test_task_status_and_subject_cascade_match_domain_contract():
    """Catches accidental status values or loss of task cascade deletion."""
    status_type = AcademicTask.__table__.c.status.type
    subject_fk = next(iter(AcademicTask.__table__.c.subject_id.foreign_keys))

    assert isinstance(status_type, Enum)
    assert set(status_type.enums) == {
        TaskStatus.PENDING.value,
        TaskStatus.IN_PROGRESS.value,
        TaskStatus.COMPLETED.value,
    }
    assert subject_fk.ondelete == "CASCADE"
    assert set(EduAIMessageRole) == {
        EduAIMessageRole.USER,
        EduAIMessageRole.ASSISTANT,
    }

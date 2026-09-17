"""Add EDU IA conversations.

Revision ID: 20260910_0003
Revises: 20260903_0002
Create Date: 2026-09-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260910_0003"
down_revision: str | Sequence[str] | None = "20260903_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

edu_ai_message_role = postgresql.ENUM(
    "user", "assistant", name="edu_ai_message_role", create_type=False
)


def upgrade() -> None:
    op.create_table(
        "edu_ai_conversations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=True),
        sa.Column("task_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["task_id"], ["academic_tasks.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_edu_ai_conversations_user_updated",
        "edu_ai_conversations",
        ["user_id", "updated_at"],
        unique=False,
    )
    edu_ai_message_role.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "edu_ai_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("role", edu_ai_message_role, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["edu_ai_conversations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_edu_ai_messages_conversation_created",
        "edu_ai_messages",
        ["conversation_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_edu_ai_messages_conversation_created", table_name="edu_ai_messages")
    op.drop_table("edu_ai_messages")
    edu_ai_message_role.drop(op.get_bind(), checkfirst=True)
    op.drop_index("ix_edu_ai_conversations_user_updated", table_name="edu_ai_conversations")
    op.drop_table("edu_ai_conversations")

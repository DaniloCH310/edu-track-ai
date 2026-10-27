"""Add spaced review missions.

Revision ID: 20260922_0004
Revises: 20260910_0003
Create Date: 2026-09-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260922_0004"
down_revision: str | Sequence[str] | None = "20260910_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

review_mission_status = postgresql.ENUM(
    "pending", "in_progress", "completed", name="review_mission_status", create_type=False
)


def upgrade() -> None:
    review_mission_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "review_missions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("status", review_mission_status, nullable=False),
        sa.Column("questions", sa.JSON(), nullable=False),
        sa.Column("answers", sa.JSON(), nullable=False),
        sa.Column("mastery_percent", sa.Integer(), nullable=True),
        sa.Column("mastery_summary", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["academic_tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id"),
    )
    op.create_index(
        "ix_review_missions_subject_due",
        "review_missions",
        ["subject_id", "due_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_review_missions_subject_due", table_name="review_missions")
    op.drop_table("review_missions")
    review_mission_status.drop(op.get_bind(), checkfirst=True)

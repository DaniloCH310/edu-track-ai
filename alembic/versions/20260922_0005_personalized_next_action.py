"""Add task effort metadata for personalized next actions.

Revision ID: 20260922_0005
Revises: 20260922_0004
Create Date: 2026-09-22
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260922_0005"
down_revision: str | Sequence[str] | None = "20260922_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "academic_tasks",
        sa.Column("difficulty", sa.Integer(), nullable=False, server_default="3"),
    )
    op.add_column(
        "academic_tasks",
        sa.Column(
            "estimated_minutes", sa.Integer(), nullable=False, server_default="30"
        ),
    )
    op.alter_column("academic_tasks", "difficulty", server_default=None)
    op.alter_column("academic_tasks", "estimated_minutes", server_default=None)


def downgrade() -> None:
    op.drop_column("academic_tasks", "estimated_minutes")
    op.drop_column("academic_tasks", "difficulty")

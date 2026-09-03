"""Add private Google Classroom integration tables.

Revision ID: 20260903_0002
Revises: 20260827_0001
Create Date: 2026-09-03
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260903_0002"
down_revision: str | Sequence[str] | None = "20260827_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS private")
    op.execute("REVOKE ALL ON SCHEMA private FROM PUBLIC")

    op.create_table(
        "classroom_connections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("encrypted_refresh_token", sa.Text(), nullable=False),
        sa.Column("granted_scopes", sa.Text(), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_code", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
        schema="private",
    )
    op.create_table(
        "classroom_course_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("connection_id", sa.Uuid(), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("classroom_course_id", sa.String(length=128), nullable=False),
        sa.Column("course_state", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["connection_id"],
            ["private.classroom_connections.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "connection_id",
            "classroom_course_id",
            name="uq_classroom_course_links_connection_course",
        ),
        sa.UniqueConstraint("subject_id"),
        schema="private",
    )
    op.create_table(
        "classroom_task_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("course_link_id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("classroom_coursework_id", sa.String(length=128), nullable=False),
        sa.Column("classroom_submission_id", sa.String(length=128), nullable=True),
        sa.Column("alternate_link", sa.Text(), nullable=False),
        sa.Column("source_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["course_link_id"],
            ["private.classroom_course_links.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["task_id"], ["academic_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "course_link_id",
            "classroom_coursework_id",
            name="uq_classroom_task_links_course_work",
        ),
        sa.UniqueConstraint("task_id"),
        schema="private",
    )

    for table in (
        "classroom_connections",
        "classroom_course_links",
        "classroom_task_links",
    ):
        op.execute(f'ALTER TABLE private."{table}" ENABLE ROW LEVEL SECURITY')
        op.execute(
            f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
                    EXECUTE 'REVOKE ALL ON TABLE private.{table} FROM anon';
                END IF;
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
                    EXECUTE 'REVOKE ALL ON TABLE private.{table} FROM authenticated';
                END IF;
            END
            $$
            """
        )


def downgrade() -> None:
    op.drop_table("classroom_task_links", schema="private")
    op.drop_table("classroom_course_links", schema="private")
    op.drop_table("classroom_connections", schema="private")
    op.execute("DROP SCHEMA private")

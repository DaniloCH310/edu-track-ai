import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.core.config import get_settings
from app.core.database import Base
from app.core.database_safety import (
    UnsafeTestDatabase,
    authorize_test_connection,
    validate_test_target,
)
from app.models import (  # noqa: F401
    AcademicTask,
    ClassroomConnection,
    ClassroomCourseLink,
    ClassroomTaskLink,
    PasswordResetToken,
    Subject,
    User,
)

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    if get_settings().environment == "test":
        raise UnsafeTestDatabase("Migração offline de teste recusada: identidade não verificável.")
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    settings = get_settings()
    github_actions = os.environ.get("GITHUB_ACTIONS") == "true"
    if settings.environment == "test":
        validate_test_target(
            settings.database_url,
            environment=settings.environment,
            github_actions=github_actions,
        )
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        if settings.environment == "test":
            authorize_test_connection(
                connection,
                environment=settings.environment,
                github_actions=github_actions,
            )
            # End the read-only identity transaction before Alembic owns its transaction.
            connection.rollback()
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

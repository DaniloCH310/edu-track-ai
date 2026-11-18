import os
from collections.abc import Generator

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings
from app.core.database_safety import protect_test_engine, validate_test_target

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


settings = get_settings()
if settings.environment == "test":
    validate_test_target(
        settings.database_url,
        environment=settings.environment,
        github_actions=os.environ.get("GITHUB_ACTIONS") == "true",
    )
engine = create_engine(settings.database_url, pool_pre_ping=True)
if settings.environment == "test":
    protect_test_engine(
        engine,
        environment=settings.environment,
        github_actions=os.environ.get("GITHUB_ACTIONS") == "true",
    )
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

import os
import runpy
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

from app.core.database_safety import (
    LOCAL_TEST_URL,
    TEST_DATABASE_MARKER,
    UnsafeTestDatabase,
    clean_test_database,
    configure_test_environment,
    protect_test_engine,
    validate_test_target,
)


@pytest.mark.parametrize(
    "url",
    [
        "postgresql+psycopg://edutrack:secret@production.example.com:5432/edutrack_test",
        "postgresql+psycopg://edutrack:secret@127.0.0.1:54329/edutrack",
        LOCAL_TEST_URL.replace("/edutrack_test", "/edutrack"),
        LOCAL_TEST_URL.replace("edutrack:", "postgres:"),
        LOCAL_TEST_URL.replace("127.0.0.1", "localhost"),
        LOCAL_TEST_URL.replace(":54330", ""),
        LOCAL_TEST_URL + "?host=production.example.com",
        LOCAL_TEST_URL + "?hostaddr=10.0.0.1",
        LOCAL_TEST_URL + "?dbname=edutrack",
        LOCAL_TEST_URL + "?options=-csearch_path=public",
        "sqlite:///:memory:",
        "not a database URL",
    ],
)
def test_unauthorized_urls_never_open_a_connection(url):
    engine = Mock(url=url)
    with pytest.raises(UnsafeTestDatabase) as error:
        clean_test_database(engine, environment="test")
    engine.begin.assert_not_called()
    assert "secret" not in str(error.value)


@pytest.mark.parametrize("environment", ["production", "development", "", "TEST"])
def test_environment_must_be_test_even_for_allowlisted_url(environment):
    engine = Mock(url=LOCAL_TEST_URL)
    with pytest.raises(UnsafeTestDatabase):
        clean_test_database(engine, environment=environment)
    engine.begin.assert_not_called()


def test_testing_boolean_does_not_authorize_production():
    env = {"TESTING": "true", "ENVIRONMENT": "production", "DATABASE_URL": LOCAL_TEST_URL}
    with pytest.raises(UnsafeTestDatabase):
        configure_test_environment(env)
    assert env["ENVIRONMENT"] == "production"


def test_inherited_development_url_is_rejected_not_silently_overwritten():
    env = {"DATABASE_URL": LOCAL_TEST_URL.replace(":54330/edutrack_test", ":54329/edutrack")}
    original = dict(env)
    with pytest.raises(UnsafeTestDatabase):
        configure_test_environment(env)
    assert env == original


def test_default_is_dedicated_test_database():
    env = {}
    configure_test_environment(env)
    assert env == {"DATABASE_URL": LOCAL_TEST_URL, "ENVIRONMENT": "test"}


def test_conflicting_explicit_test_url_is_rejected():
    env = {"DATABASE_URL": LOCAL_TEST_URL, "TEST_DATABASE_URL": LOCAL_TEST_URL + "?host=remote"}
    with pytest.raises(UnsafeTestDatabase):
        configure_test_environment(env)


def test_ci_only_allows_its_fixed_service_target():
    ci_url = LOCAL_TEST_URL.replace(":54330", ":5432")
    assert validate_test_target(ci_url, environment="test", github_actions=True).port == 5432
    with pytest.raises(UnsafeTestDatabase):
        validate_test_target(ci_url, environment="test")
    with pytest.raises(UnsafeTestDatabase):
        validate_test_target(
            ci_url.replace("127.0.0.1", "remote"),
            environment="test",
            github_actions=True,
        )


class FakeEngine:
    """Records statements without creating any real database connection."""

    def __init__(self, row):
        self.url = make_url(LOCAL_TEST_URL)
        self.row = row
        self.statements = []

    @contextmanager
    def begin(self):
        yield self

    @property
    def engine(self):
        return self

    def execute(self, sql):
        self.statements.append(str(sql))
        return Mock(one_or_none=lambda: self.row)


@pytest.mark.parametrize(
    "row",
    [
        None,
        ("edutrack_test", "edutrack", "edutrack", 54330, None),
        ("edutrack", "edutrack", "edutrack", 54330, TEST_DATABASE_MARKER),
        ("edutrack_test", "postgres", "edutrack", 54330, TEST_DATABASE_MARKER),
        ("edutrack_test", "edutrack", "postgres", 54330, TEST_DATABASE_MARKER),
        ("edutrack_test", "edutrack", "edutrack", 54329, TEST_DATABASE_MARKER),
        ("edutrack_test", "edutrack", "edutrack", 54330, "TESTING=true"),
    ],
)
def test_runtime_identity_or_missing_marker_blocks_truncate(row):
    engine = FakeEngine(row)
    with pytest.raises(UnsafeTestDatabase):
        clean_test_database(engine, environment="test")
    assert len(engine.statements) == 1
    assert engine.statements[0].lstrip().startswith("SELECT")


def test_cleanup_revalidates_every_time_including_teardown():
    engine = FakeEngine(("edutrack_test", "edutrack", "edutrack", 54330, TEST_DATABASE_MARKER))
    clean_test_database(engine, environment="test")
    assert [sql.lstrip().split()[0] for sql in engine.statements] == ["SELECT", "TRUNCATE"]
    engine.row = None
    with pytest.raises(UnsafeTestDatabase):
        clean_test_database(engine, environment="test")
    assert [sql.lstrip().split()[0] for sql in engine.statements] == [
        "SELECT",
        "TRUNCATE",
        "SELECT",
    ]


def test_dbapi_guard_runs_before_connection_is_exposed():
    # Engine construction does not connect. Call its registered event with a fake DBAPI connection.
    engine = create_engine(LOCAL_TEST_URL)
    protect_test_engine(engine, environment="test")
    cursor = Mock()
    cursor.fetchone.return_value = ("edutrack_test", "edutrack", "edutrack", 54330, None)
    dbapi = Mock()
    dbapi.cursor.return_value.__enter__ = Mock(return_value=cursor)
    dbapi.cursor.return_value.__exit__ = Mock(return_value=False)
    # Only the guard is added as the final listener; no connection or SQL reaches PostgreSQL.
    guard = list(engine.pool.dispatch.connect)[-1]
    with pytest.raises(UnsafeTestDatabase):
        guard(dbapi, None)
    dbapi.rollback.assert_called_once()
    assert cursor.execute.call_count == 1
    assert cursor.execute.call_args.args[0].lstrip().startswith("SELECT")
    engine.dispose()


def test_pytest_bootstrap_rejects_external_url_before_collecting_tests():
    env = dict(os.environ)
    env.update(
        {
            "ENVIRONMENT": "test",
            "TESTING": "true",
            "DATABASE_URL": "postgresql+psycopg://edutrack:do-not-print@db.invalid:5432/edutrack",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "tests/unit/test_security.py",
            "--collect-only",
            "-p",
            "no:cacheprovider",
            "-q",
        ],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "UnsafeTestDatabase" in output
    assert "do-not-print" not in output


@pytest.mark.parametrize("marker", [None, TEST_DATABASE_MARKER])
def test_test_migrations_require_identity_before_running(monkeypatch, marker):
    import app.core.database  # noqa: F401 - construct engine without connecting before patching
    from alembic import context

    fake_config = Mock(config_file_name=None, config_ini_section="alembic")
    fake_config.get_section.return_value = {}
    monkeypatch.setattr(context, "config", fake_config, raising=False)
    monkeypatch.setattr(context, "is_offline_mode", lambda: False)
    monkeypatch.setattr(context, "configure", Mock())
    monkeypatch.setattr(context, "begin_transaction", MagicMock())
    run_migrations = Mock()
    monkeypatch.setattr(context, "run_migrations", run_migrations)
    monkeypatch.setattr(
        "app.core.config.get_settings",
        lambda: SimpleNamespace(
            environment="test",
            database_url=LOCAL_TEST_URL,
        ),
    )
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    engine = MagicMock(url=make_url(LOCAL_TEST_URL))
    connection = engine.connect.return_value.__enter__.return_value
    connection.engine = engine
    connection.execute.return_value.one_or_none.return_value = (
        "edutrack_test",
        "edutrack",
        "edutrack",
        54330,
        marker,
    )
    monkeypatch.setattr("sqlalchemy.engine_from_config", Mock(return_value=engine))
    path = Path(__file__).resolve().parents[2] / "alembic/env.py"
    if marker is None:
        with pytest.raises(UnsafeTestDatabase):
            runpy.run_path(str(path))
        run_migrations.assert_not_called()
    else:
        runpy.run_path(str(path))
        run_migrations.assert_called_once()
        connection.rollback.assert_called_once()
    connection.execute.assert_called_once()
    assert str(connection.execute.call_args.args[0]).lstrip().startswith("SELECT")


def test_ci_cleanup_uses_same_database_marker():
    engine = FakeEngine(("edutrack_test", "edutrack", "edutrack", 5432, TEST_DATABASE_MARKER))
    engine.url = make_url(LOCAL_TEST_URL.replace(":54330", ":5432"))
    clean_test_database(engine, environment="test", github_actions=True)
    assert [sql.lstrip().split()[0] for sql in engine.statements] == ["SELECT", "TRUNCATE"]

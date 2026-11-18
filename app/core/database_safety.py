"""Fail-closed authorization for disposable PostgreSQL test databases only."""

from collections.abc import MutableMapping

from sqlalchemy import event, text
from sqlalchemy.engine import URL, Connection, Engine, make_url
from sqlalchemy.exc import ArgumentError

TEST_DATABASE_MARKER = "edutrack:disposable-test-database:v1"
LOCAL_TEST_URL = "postgresql+psycopg://edutrack:edutrack_test@127.0.0.1:54330/edutrack_test"
IDENTITY_SQL = """
SELECT current_database(), current_user, session_user, inet_server_port(),
       shobj_description(oid, 'pg_database')
FROM pg_database WHERE datname = current_database()
"""
TRUNCATE_SQL = """
TRUNCATE TABLE review_missions, edu_ai_messages, edu_ai_conversations,
private.classroom_task_links, private.classroom_course_links, private.classroom_connections,
password_reset_tokens, academic_tasks, subjects, users RESTART IDENTITY CASCADE
"""


class UnsafeTestDatabase(RuntimeError):
    """Authorization failed; never include credentials in this error."""


def validate_test_target(
    value: str | URL,
    *,
    environment: str,
    github_actions: bool = False,
) -> URL:
    if environment != "test":
        raise UnsafeTestDatabase("Operação de teste recusada: ENVIRONMENT deve ser test.")
    try:
        url = make_url(value)
        allowed = (
            url.drivername == "postgresql+psycopg"
            and url.host == "127.0.0.1"
            and url.database == "edutrack_test"
            and url.username == "edutrack"
            and url.port in ({5432} if github_actions else {54330})
            and not url.query
        )
    except (ArgumentError, TypeError, ValueError):
        allowed = False
    if not allowed:
        raise UnsafeTestDatabase(
            "Destino de testes não autorizado. Use o PostgreSQL local dedicado "
            "(porta 54330) ou o serviço descartável do GitHub Actions (porta 5432), "
            "banco edutrack_test, usuário edutrack, sem parâmetros extras na URL."
        ) from None
    return url


def configure_test_environment(environ: MutableMapping[str, str]) -> None:
    """Reject unsafe inherited values before importing application settings/engine."""
    environment = environ.get("ENVIRONMENT", "test")
    github_actions = environ.get("GITHUB_ACTIONS") == "true"
    value = environ.get("DATABASE_URL", environ.get("TEST_DATABASE_URL", LOCAL_TEST_URL))
    target = validate_test_target(value, environment=environment, github_actions=github_actions)
    if "TEST_DATABASE_URL" in environ:
        explicit = validate_test_target(
            environ["TEST_DATABASE_URL"],
            environment=environment,
            github_actions=github_actions,
        )
        if explicit != target:
            raise UnsafeTestDatabase(
                "DATABASE_URL e TEST_DATABASE_URL divergem; execução recusada."
            )
    environ["DATABASE_URL"] = value
    environ["ENVIRONMENT"] = "test"


def validate_test_identity(row, expected_port: int) -> None:
    if row is None or tuple(row) != (
        "edutrack_test",
        "edutrack",
        "edutrack",
        expected_port,
        TEST_DATABASE_MARKER,
    ):
        raise UnsafeTestDatabase(
            "Banco recusado: identidade PostgreSQL ou marca de banco descartável inválida. "
            "Não autorize um banco existente sem verificar que ele contém somente dados de teste."
        )


def authorize_test_connection(
    connection: Connection,
    *,
    environment: str,
    github_actions: bool = False,
) -> None:
    url = validate_test_target(
        connection.engine.url,
        environment=environment,
        github_actions=github_actions,
    )
    validate_test_identity(connection.execute(text(IDENTITY_SQL)).one_or_none(), url.port)


def protect_test_engine(engine: Engine, *, environment: str, github_actions: bool = False) -> None:
    """Verify every new DBAPI connection before fixtures can read/write through it."""
    url = validate_test_target(engine.url, environment=environment, github_actions=github_actions)

    @event.listens_for(engine, "connect")
    def check_identity(dbapi_connection, _record):
        try:
            with dbapi_connection.cursor() as cursor:
                cursor.execute(IDENTITY_SQL)
                validate_test_identity(cursor.fetchone(), url.port)
        finally:
            dbapi_connection.rollback()


def clean_test_database(engine: Engine, *, environment: str, github_actions: bool = False) -> None:
    # URL/environment validation must precede even opening a connection.
    validate_test_target(engine.url, environment=environment, github_actions=github_actions)
    with engine.begin() as connection:
        # Recheck on the same connection/transaction, including fixture teardown.
        authorize_test_connection(
            connection,
            environment=environment,
            github_actions=github_actions,
        )
        connection.execute(text(TRUNCATE_SQL))

import base64
import os
import secrets
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Settings


@pytest.fixture
def config(monkeypatch):
    monkeypatch.delenv("JWT_SECRET", raising=False)
    return {
        "_env_file": None,
        "environment": "production",
        "database_url": "postgresql+psycopg://unused:unused@db.invalid/unused",
        "smtp_username": "tests@example.com",
        "smtp_password": "private-smtp-marker",
        "smtp_from_email": "tests@example.com",
        "cookie_secure": True,
        "frontend_url": "https://edutrack.example.com",
        "google_classroom_enabled": False,
        "edu_ai_enabled": False,
    }


@pytest.mark.parametrize(
    "secret",
    [
        "",
        "short",
        "a" * 64,
        "abcd" * 16,
        "0123456789" * 8,
        "abcdefghijklmnopqrstuvwxyz" * 3,
        "qwertyuiopasdfghjklzxcvbnm" * 3,
        "troque-por-uma-chave-aleatoria-longa",
        "test-secret-with-at-least-thirty-two-characters",
        "ci-secret-with-at-least-thirty-two-characters",
        "a-long-random-production-secret",
        "change-me-to-a-long-random-secret-key",
        "correct-horse-battery-staple-correct-horse-battery-staple",
        "a" * 100 + "BCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        " " + "aBcD1eF2gH3iJ4kL5mN6oP7qR8sT9uV0wX",
    ],
    ids=[
        "empty",
        "short",
        "constant",
        "periodic",
        "digits",
        "alphabet",
        "keyboard",
        "local-example",
        "test-example",
        "ci-example",
        "old-test-example",
        "placeholder",
        "known-passphrase",
        "low-diversity",
        "whitespace",
    ],
)
def test_production_rejects_weak_secrets_without_logging_values(config, secret, caplog):
    with pytest.raises(ValidationError) as caught:
        Settings(**config, jwt_secret=secret)
    rendered = str(caught.value) + repr(caught.value) + caplog.text
    assert "JWT_SECRET" in rendered
    if secret:
        assert secret not in rendered
    assert config["smtp_password"] not in rendered


def test_missing_secret_is_rejected_without_dumping_other_credentials(config):
    with pytest.raises(ValidationError) as caught:
        Settings(**config)
    assert "jwt_secret" in str(caught.value)
    assert config["smtp_password"] not in str(caught.value)


@pytest.mark.parametrize("encoding", ["urlsafe", "base64", "hex"])
def test_generated_secret_is_accepted_unchanged(config, encoding):
    raw = secrets.token_bytes(32)
    secret = {
        "urlsafe": base64.urlsafe_b64encode(raw).decode(),
        "base64": base64.b64encode(raw).decode(),
        "hex": raw.hex(),
    }[encoding]
    settings = Settings(**config, jwt_secret=secret)
    assert settings.jwt_secret == secret
    assert secret not in repr(settings)


@pytest.mark.parametrize("environment", ["development", "test"])
def test_nonproduction_keeps_existing_behavior(config, environment):
    config["environment"] = environment
    assert Settings(**config, jwt_secret="local-example").jwt_secret == "local-example"


def test_production_environment_cannot_bypass_check_with_case_or_spaces(config):
    config["environment"] = " Production "
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(**config, jwt_secret="weak")


def test_startup_rejects_secret_before_database_engine_or_requests(config):
    env = dict(os.environ)
    env.update({key.upper(): str(value) for key, value in config.items() if key != "_env_file"})
    env["JWT_SECRET"] = "startup-private-weak-marker"
    code = (
        "import sqlalchemy\n"
        "def forbidden(*args, **kwargs):\n"
        "    raise AssertionError('DATABASE_ENGINE_WAS_CREATED')\n"
        "sqlalchemy.create_engine = forbidden\n"
        "import app.main\n"
    )
    result = subprocess.run(
        [sys.executable, "-B", "-c", code],
        env=env,
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "ValidationError" in output and "JWT_SECRET" in output
    assert "DATABASE_ENGINE_WAS_CREATED" not in output
    assert env["JWT_SECRET"] not in output
    assert config["smtp_password"] not in output

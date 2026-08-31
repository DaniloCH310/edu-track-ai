import pytest
from pydantic import ValidationError

from app.core.config import Settings

REQUIRED_SETTINGS = {
    "database_url": "postgresql+psycopg://user:password@db.example.com:5432/edutrack",
    "jwt_secret": "a-long-random-production-secret",
    "smtp_username": "mailer@example.com",
    "smtp_password": "app-password",
    "smtp_from_email": "mailer@example.com",
}


def test_production_rejects_insecure_session_cookie():
    with pytest.raises(ValidationError, match="COOKIE_SECURE"):
        Settings(
            environment="production",
            frontend_url="https://edutrack.example.com",
            cookie_secure=False,
            **REQUIRED_SETTINGS,
        )


def test_production_rejects_non_https_frontend_url():
    with pytest.raises(ValidationError, match="FRONTEND_URL"):
        Settings(
            environment="production",
            frontend_url="http://edutrack.example.com",
            cookie_secure=True,
            **REQUIRED_SETTINGS,
        )


def test_production_accepts_secure_settings():
    settings = Settings(
        environment="production",
        frontend_url="https://edutrack.example.com",
        cookie_secure=True,
        **REQUIRED_SETTINGS,
    )

    assert settings.environment == "production"

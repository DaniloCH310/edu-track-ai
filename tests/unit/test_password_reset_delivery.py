"""Exercise the HTTP contract using fake persistence and SMTP, never a real database."""

import logging
import smtplib
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.auth import router
from app.core.config import get_settings
from app.core.database import get_db
from app.repositories.users import UserRepository
from app.services import auth as auth_module
from app.services import email as email_module

TOKEN = "private-reset-token"
PASSWORD = "private-smtp-password"
ADDRESS = "private-student@example.com"
SENSITIVE = f"{TOKEN} {PASSWORD} {ADDRESS} private-smtp-user@example.com"


@pytest.mark.parametrize(
    "stage,error",
    [
        (None, None),
        ("connect", ConnectionRefusedError(SENSITIVE)),
        ("connect", TimeoutError(SENSITIVE)),
        ("starttls", smtplib.SMTPException(SENSITIVE)),
        ("login", smtplib.SMTPAuthenticationError(535, SENSITIVE.encode())),
        ("send", TimeoutError(SENSITIVE)),
        ("send", smtplib.SMTPDataError(550, SENSITIVE.encode())),
        ("quit", smtplib.SMTPServerDisconnected(SENSITIVE)),
    ],
)
def test_reset_http_response_is_neutral_on_delivery_failure(monkeypatch, caplog, stage, error):
    db = Mock()
    lookup = Mock(return_value=SimpleNamespace(id=1, email=ADDRESS, is_active=True))
    create_token = Mock()
    invalidate = Mock()
    monkeypatch.setattr(UserRepository, "get_by_email", lookup)
    monkeypatch.setattr(UserRepository, "create_reset_token", create_token)
    monkeypatch.setattr(UserRepository, "invalidate_reset_tokens", invalidate)
    monkeypatch.setattr(auth_module, "generate_reset_token", lambda: (TOKEN, "hashed-token"))
    settings = get_settings().model_copy(
        update={
            "smtp_username": "private-smtp-user@example.com",
            "smtp_password": PASSWORD,
        }
    )
    monkeypatch.setattr(email_module, "get_settings", lambda: settings)
    calls = []

    def operation(name):
        calls.append(name)
        if stage == name:
            raise error

    class FakeSMTP:
        def __init__(self, *args, **kwargs):
            operation("connect")

        def __enter__(self):
            return self

        def __exit__(self, *args):
            operation("quit")

        def starttls(self, **kwargs):
            operation("starttls")

        def login(self, *args):
            operation("login")

        def send_message(self, message):
            assert TOKEN in message.get_content()
            operation("send")

    monkeypatch.setattr(email_module.smtplib, "SMTP", FakeSMTP)
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db
    before = datetime.now(UTC)
    with caplog.at_level(logging.WARNING), TestClient(app) as client:
        known = client.post("/api/auth/forgot-password", json={"email": ADDRESS})
        call_count = len(calls)
        lookup.return_value = None
        unknown = client.post("/api/auth/forgot-password", json={"email": "absent@example.com"})
        lookup.return_value = SimpleNamespace(id=2, email=ADDRESS, is_active=False)
        inactive = client.post("/api/auth/forgot-password", json={"email": ADDRESS})

    assert known.status_code == unknown.status_code == inactive.status_code == 202
    assert known.json() == unknown.json() == inactive.json()
    assert len(calls) == call_count  # Neither absent nor inactive accounts send mail.
    create_token.assert_called_once()
    token_data = create_token.call_args.kwargs
    assert token_data["token_hash"] == "hashed-token"
    assert before + timedelta(minutes=settings.password_reset_minutes) <= token_data["expires_at"]
    assert token_data["expires_at"] <= datetime.now(UTC) + timedelta(
        minutes=settings.password_reset_minutes
    )
    invalidate.assert_called_once()
    if stage is None:
        db.commit.assert_called_once()
        db.rollback.assert_not_called()
        assert "send" in calls
        assert not caplog.records
    else:
        db.rollback.assert_called_once()
        db.commit.assert_not_called()
        assert len(caplog.records) == 1
        assert caplog.records[0].exc_info is None
    for secret in SENSITIVE.split():
        assert secret not in caplog.text + known.text + unknown.text + inactive.text

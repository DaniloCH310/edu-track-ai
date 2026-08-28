from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

import pytest
from sqlalchemy import select

from app.core.security import generate_reset_token
from app.models.user import PasswordResetToken
from app.services.email import EmailService


@pytest.fixture
def reset_token_factory(db_session, user_factory):
    def create_token(*, email: str = "ana@example.com", expired: bool = False) -> str:
        user = user_factory(email=email)
        raw_token, token_hash = generate_reset_token()
        record = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC)
            + (timedelta(minutes=-1) if expired else timedelta(minutes=30)),
        )
        db_session.add(record)
        db_session.commit()
        return raw_token

    return create_token


def test_forgot_password_is_neutral_and_only_emails_known_user(
    client, user_factory, db_session, monkeypatch
):
    user_factory(email="ana@example.com")
    sent: list[tuple[str, str]] = []

    def capture_email(_service, *, to_email: str, reset_url: str) -> None:
        sent.append((to_email, reset_url))

    monkeypatch.setattr(EmailService, "send_password_reset", capture_email)

    known = client.post(
        "/api/auth/forgot-password", json={"email": "ANA@example.com"}
    )
    unknown = client.post(
        "/api/auth/forgot-password", json={"email": "ninguem@example.com"}
    )

    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()
    assert len(sent) == 1
    assert sent[0][0] == "ana@example.com"
    assert "reset_token=" in sent[0][1]
    raw_token = parse_qs(urlparse(sent[0][1]).query)["reset_token"][0]
    stored = db_session.scalar(select(PasswordResetToken))
    assert stored is not None
    assert stored.token_hash != raw_token
    assert raw_token not in stored.token_hash


def test_reset_token_is_single_use_and_changes_password(
    client, reset_token_factory
):
    raw_token = reset_token_factory()
    payload = {"token": raw_token, "new_password": "Nova-Senha-456"}

    assert client.post("/api/auth/reset-password", json=payload).status_code == 204
    reused = client.post("/api/auth/reset-password", json=payload)

    assert reused.status_code == 400
    assert reused.json()["error"]["code"] == "invalid_reset_token"
    assert client.post(
        "/api/auth/login",
        json={"email": "ana@example.com", "password": "Nova-Senha-456"},
    ).status_code == 200


def test_expired_reset_token_is_rejected(client, reset_token_factory):
    raw_token = reset_token_factory(expired=True)

    response = client.post(
        "/api/auth/reset-password",
        json={"token": raw_token, "new_password": "Nova-Senha-456"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_reset_token"

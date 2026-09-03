import base64
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.integrations.google_classroom.crypto import (
    decrypt_refresh_token,
    encrypt_refresh_token,
)
from app.integrations.google_classroom.oauth import (
    InvalidOAuthState,
    create_oauth_context,
    validate_oauth_context,
)

USER_ID = UUID("11111111-1111-4111-8111-111111111111")
OTHER_USER_ID = UUID("22222222-2222-4222-8222-222222222222")
SECRET = "oauth-state-secret-with-at-least-thirty-two-characters"
NOW = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)
FERNET_KEY = base64.urlsafe_b64encode(b"k" * 32).decode()


def settings_values() -> dict[str, object]:
    return {
        "database_url": "postgresql+psycopg://local/test",
        "jwt_secret": "test-secret-with-at-least-thirty-two-characters",
        "smtp_username": "tests@example.com",
        "smtp_password": "not-a-real-password",
        "smtp_from_email": "tests@example.com",
    }


def test_refresh_token_round_trip_never_returns_plaintext():
    encrypted = encrypt_refresh_token("fake-refresh-value", FERNET_KEY)

    assert encrypted != "fake-refresh-value"
    assert decrypt_refresh_token(encrypted, FERNET_KEY) == "fake-refresh-value"


def test_invalid_fernet_key_is_rejected_without_echoing_it():
    with pytest.raises(ValueError, match="GOOGLE_TOKEN_ENCRYPTION_KEY") as captured:
        encrypt_refresh_token("fake-refresh-value", "invalid-key")

    assert "invalid-key" not in str(captured.value)


def test_enabled_classroom_requires_complete_configuration():
    with pytest.raises(ValidationError, match="Google Classroom"):
        Settings(**settings_values(), google_classroom_enabled=True)


def test_oauth_context_is_bound_to_state_and_user():
    context = create_oauth_context(USER_ID, SECRET, now=NOW)

    assert validate_oauth_context(
        context.cookie, context.state, USER_ID, SECRET, now=NOW
    ) == context.verifier
    with pytest.raises(InvalidOAuthState):
        validate_oauth_context(context.cookie, "different", USER_ID, SECRET, now=NOW)
    with pytest.raises(InvalidOAuthState):
        validate_oauth_context(
            context.cookie, context.state, OTHER_USER_ID, SECRET, now=NOW
        )


def test_oauth_context_uses_s256_pkce_and_expires_after_ten_minutes():
    context = create_oauth_context(USER_ID, SECRET, now=NOW)

    assert context.challenge != context.verifier
    assert "=" not in context.challenge
    with pytest.raises(InvalidOAuthState):
        validate_oauth_context(
            context.cookie,
            context.state,
            USER_ID,
            SECRET,
            now=NOW + timedelta(minutes=11),
        )

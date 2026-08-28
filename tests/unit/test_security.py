import hashlib
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from app.core.config import get_settings
from app.core.security import (
    InvalidSessionToken,
    create_access_token,
    decode_access_token,
    generate_reset_token,
    hash_password,
    verify_password,
)


def test_password_hash_hides_plaintext_and_rejects_wrong_password():
    """Catches plaintext storage and verification that accepts an unrelated password."""
    encoded = hash_password("Senha-Forte-123")

    assert "Senha-Forte-123" not in encoded
    assert verify_password("Senha-Forte-123", encoded)
    assert not verify_password("senha-incorreta", encoded)


def test_access_token_round_trip_preserves_user_id():
    """Catches a JWT whose subject cannot identify the authenticated user."""
    user_id = uuid4()

    token = create_access_token(user_id)

    assert decode_access_token(token) == user_id


def test_expired_access_token_is_rejected():
    """Catches accepting a correctly signed but expired browser session."""
    settings = get_settings()
    user_id = uuid4()
    expired = jwt.encode(
        {
            "sub": str(user_id),
            "type": "access",
            "iat": datetime.now(UTC) - timedelta(hours=2),
            "exp": datetime.now(UTC) - timedelta(hours=1),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )

    with pytest.raises(InvalidSessionToken):
        decode_access_token(expired)


def test_reset_token_returns_plain_value_and_only_its_sha256_digest():
    """Catches persisting a password-reset credential in recoverable plaintext."""
    raw_token, token_hash = generate_reset_token()

    assert len(raw_token) >= 40
    assert len(token_hash) == 64
    assert raw_token != token_hash
    assert all(character in "0123456789abcdef" for character in token_hash)
    assert token_hash == hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

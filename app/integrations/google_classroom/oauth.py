import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

OAUTH_AUDIENCE = "google-classroom-oauth"
OAUTH_CONTEXT_MINUTES = 10


class InvalidOAuthState(ValueError):
    """Raised when an OAuth callback cannot be tied to its browser request."""


@dataclass(frozen=True)
class OAuthContext:
    state: str
    verifier: str
    challenge: str
    cookie: str


def create_oauth_context(
    user_id: UUID, secret: str, now: datetime | None = None
) -> OAuthContext:
    issued_at = now or datetime.now(UTC)
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    cookie = jwt.encode(
        {
            "sub": str(user_id),
            "state": state,
            "verifier": verifier,
            "aud": OAUTH_AUDIENCE,
            "iat": int(issued_at.timestamp()),
            "exp": int((issued_at + timedelta(minutes=OAUTH_CONTEXT_MINUTES)).timestamp()),
        },
        secret,
        algorithm="HS256",
    )
    return OAuthContext(state=state, verifier=verifier, challenge=challenge, cookie=cookie)


def validate_oauth_context(
    cookie: str,
    returned_state: str,
    user_id: UUID,
    secret: str,
    now: datetime | None = None,
) -> str:
    checked_at = now or datetime.now(UTC)
    try:
        payload = jwt.decode(
            cookie,
            secret,
            algorithms=["HS256"],
            audience=OAUTH_AUDIENCE,
            options={"verify_exp": False},
        )
        expires_at = int(payload["exp"])
        stored_state = str(payload["state"])
        stored_user = str(payload["sub"])
        verifier = str(payload["verifier"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError) as exception:
        raise InvalidOAuthState("O contexto OAuth é inválido.") from exception

    valid = (
        expires_at >= int(checked_at.timestamp())
        and hmac.compare_digest(stored_state, returned_state)
        and hmac.compare_digest(stored_user, str(user_id))
    )
    if not valid:
        raise InvalidOAuthState("O contexto OAuth é inválido.")
    return verifier

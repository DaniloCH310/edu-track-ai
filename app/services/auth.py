from datetime import UTC, datetime, timedelta
from urllib.parse import quote

from sqlalchemy.orm import Session

from app.api.errors import ApiError
from app.core.config import get_settings
from app.core.security import (
    generate_reset_token,
    hash_password,
    hash_reset_token,
    verify_password,
)
from app.models.user import User
from app.repositories.users import UserRepository
from app.schemas.auth import RegisterInput
from app.services.email import EmailService

DUMMY_PASSWORD_HASH = hash_password("Senha-Falsa-000")


class AuthService:
    @staticmethod
    def register(db: Session, data: RegisterInput) -> User:
        if UserRepository.get_by_email(db, str(data.email)) is not None:
            raise ApiError(
                status_code=409,
                code="email_unavailable",
                message="Este e-mail não está disponível.",
            )

        user = UserRepository.create(
            db,
            name=data.name,
            email=str(data.email),
            password_hash=hash_password(data.password),
        )
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate(db: Session, *, email: str, password: str) -> User:
        user = UserRepository.get_by_email(db, email)
        encoded = user.password_hash if user is not None else DUMMY_PASSWORD_HASH
        password_is_valid = verify_password(password, encoded)
        if user is None or not user.is_active or not password_is_valid:
            raise ApiError(
                status_code=401,
                code="invalid_credentials",
                message="E-mail ou senha inválidos.",
            )
        return user

    @staticmethod
    def request_password_reset(
        db: Session, *, email: str, email_service: EmailService | None = None
    ) -> None:
        user = UserRepository.get_by_email(db, email)
        if user is None or not user.is_active:
            return

        settings = get_settings()
        now = datetime.now(UTC)
        UserRepository.invalidate_reset_tokens(db, user_id=user.id, used_at=now)
        raw_token, token_hash = generate_reset_token()
        UserRepository.create_reset_token(
            db,
            user_id=user.id,
            token_hash=token_hash,
            expires_at=now + timedelta(minutes=settings.password_reset_minutes),
        )
        reset_url = (
            f"{settings.frontend_url.rstrip('/')}/?reset_token="
            f"{quote(raw_token, safe='')}"
        )
        (email_service or EmailService()).send_password_reset(
            to_email=user.email, reset_url=reset_url
        )
        db.commit()

    @staticmethod
    def reset_password(db: Session, *, raw_token: str, new_password: str) -> None:
        now = datetime.now(UTC)
        token = UserRepository.get_valid_reset_token(
            db, token_hash=hash_reset_token(raw_token), now=now
        )
        if token is None:
            raise ApiError(
                status_code=400,
                code="invalid_reset_token",
                message="O link de redefinição é inválido ou expirou.",
            )

        token.user.password_hash = hash_password(new_password)
        UserRepository.invalidate_reset_tokens(
            db, user_id=token.user_id, used_at=now
        )
        db.commit()

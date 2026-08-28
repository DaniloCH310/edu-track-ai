from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.user import PasswordResetToken, User


class UserRepository:
    @staticmethod
    def get_by_id(db: Session, user_id: UUID) -> User | None:
        return db.scalar(select(User).where(User.id == user_id))

    @staticmethod
    def get_by_email(db: Session, email: str) -> User | None:
        return db.scalar(select(User).where(User.email == email.strip().lower()))

    @staticmethod
    def create(
        db: Session, *, name: str, email: str, password_hash: str
    ) -> User:
        user = User(name=name, email=email.strip().lower(), password_hash=password_hash)
        db.add(user)
        db.flush()
        return user

    @staticmethod
    def invalidate_reset_tokens(
        db: Session, *, user_id: UUID, used_at: datetime
    ) -> None:
        db.execute(
            update(PasswordResetToken)
            .where(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.used_at.is_(None),
            )
            .values(used_at=used_at)
        )

    @staticmethod
    def create_reset_token(
        db: Session,
        *,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> PasswordResetToken:
        token = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        db.add(token)
        db.flush()
        return token

    @staticmethod
    def get_valid_reset_token(
        db: Session, *, token_hash: str, now: datetime
    ) -> PasswordResetToken | None:
        return db.scalar(
            select(PasswordResetToken)
            .where(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > now,
            )
            .with_for_update()
        )

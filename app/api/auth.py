from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordInput,
    LoginInput,
    MessageOutput,
    RegisterInput,
    ResetPasswordInput,
    UserOutput,
)
from app.services.auth import AuthService

router = APIRouter(prefix="/api/auth", tags=["autenticação"])


def set_session_cookie(response: Response, user_id: UUID) -> None:
    settings = get_settings()
    response.set_cookie(
        key="edutrack_session",
        value=create_access_token(user_id),
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.jwt_expire_minutes * 60,
        path="/",
    )


@router.post("/register", response_model=UserOutput, status_code=status.HTTP_201_CREATED)
def register(
    data: RegisterInput,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    user = AuthService.register(db, data)
    set_session_cookie(response, user.id)
    return user


@router.post("/login", response_model=UserOutput)
def login(
    data: LoginInput,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    user = AuthService.authenticate(
        db, email=str(data.email), password=data.password
    )
    set_session_cookie(response, user.id)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    response.delete_cookie(
        key="edutrack_session",
        path="/",
        secure=get_settings().cookie_secure,
        httponly=True,
        samesite="lax",
    )


@router.post(
    "/forgot-password",
    response_model=MessageOutput,
    status_code=status.HTTP_202_ACCEPTED,
)
def forgot_password(
    data: ForgotPasswordInput,
    db: Annotated[Session, Depends(get_db)],
) -> MessageOutput:
    AuthService.request_password_reset(db, email=str(data.email))
    return MessageOutput(
        message="Se o e-mail estiver cadastrado, enviaremos as instruções."
    )


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(
    data: ResetPasswordInput,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    AuthService.reset_password(
        db, raw_token=data.token, new_password=data.new_password
    )


@router.get("/me", response_model=UserOutput)
def current_user(user: CurrentUser) -> User:
    return user

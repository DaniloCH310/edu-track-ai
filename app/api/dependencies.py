from typing import Annotated

from fastapi import Cookie, Depends
from sqlalchemy.orm import Session

from app.api.errors import ApiError
from app.core.database import get_db
from app.core.security import InvalidSessionToken, decode_access_token
from app.models.user import User
from app.repositories.users import UserRepository

NOT_AUTHENTICATED = ApiError(
    status_code=401,
    code="not_authenticated",
    message="Sua sessão não é válida. Entre novamente.",
)


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    session_token: Annotated[str | None, Cookie(alias="edutrack_session")] = None,
) -> User:
    if session_token is None:
        raise NOT_AUTHENTICATED

    try:
        user_id = decode_access_token(session_token)
    except InvalidSessionToken as exception:
        raise NOT_AUTHENTICATED from exception

    user = UserRepository.get_by_id(db, user_id)
    if user is None or not user.is_active:
        raise NOT_AUTHENTICATED
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Query, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.api.errors import ApiError
from app.core.config import get_settings
from app.core.database import get_db
from app.integrations.google_classroom.client import (
    REQUIRED_SCOPES,
    GoogleClassroomClient,
    GoogleClassroomError,
)
from app.integrations.google_classroom.crypto import encrypt_refresh_token
from app.integrations.google_classroom.oauth import (
    InvalidOAuthState,
    create_oauth_context,
    validate_oauth_context,
)
from app.integrations.google_classroom.sync import ClassroomSyncService
from app.repositories.classroom import ClassroomRepository
from app.schemas.classroom import ClassroomStatus, ClassroomSyncResult

router = APIRouter(prefix="/api/integrations/classroom", tags=["integrações"])
OAUTH_COOKIE = "edutrack_google_oauth"
CALLBACK_TARGETS = {
    "connected": "/?classroom=connected#integrations",
    "access_denied": "/?classroom=access_denied#integrations",
    "invalid_state": "/?classroom=invalid_state#integrations",
    "access_blocked": "/?classroom=access_blocked#integrations",
    "failed": "/?classroom=failed#integrations",
}


def get_classroom_client() -> GoogleClassroomClient:
    settings = get_settings()
    if not settings.google_classroom_enabled:
        raise ApiError(
            status_code=503,
            code="classroom_unavailable",
            message="A integração com Google Classroom não está configurada.",
        )
    assert settings.google_client_id is not None
    assert settings.google_client_secret is not None
    return GoogleClassroomClient(
        settings.google_client_id,
        settings.google_client_secret,
        settings.google_oauth_redirect_uri,
    )


def _redirect(target: str) -> RedirectResponse:
    settings = get_settings()
    response = RedirectResponse(CALLBACK_TARGETS[target])
    response.delete_cookie(
        OAUTH_COOKIE,
        path="/api/integrations/classroom",
        secure=settings.cookie_secure,
        httponly=True,
        samesite="lax",
    )
    return response


@router.get("", response_model=ClassroomStatus)
def classroom_status(
    user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> ClassroomStatus:
    settings = get_settings()
    if not settings.google_classroom_enabled:
        return ClassroomStatus(available=False, connected=False)
    connection = ClassroomRepository.get_connection(db, user.id)
    return ClassroomStatus(
        available=True,
        connected=connection is not None,
        last_synced_at=connection.last_synced_at if connection else None,
        last_error_code=connection.last_error_code if connection else None,
    )


@router.get("/authorize")
def authorize(
    user: CurrentUser,
    client: Annotated[GoogleClassroomClient, Depends(get_classroom_client)],
) -> RedirectResponse:
    settings = get_settings()
    context = create_oauth_context(user.id, settings.jwt_secret)
    response = RedirectResponse(client.authorization_url(context.state, context.challenge))
    response.set_cookie(
        OAUTH_COOKIE,
        context.cookie,
        max_age=600,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/api/integrations/classroom",
    )
    return response


@router.get("/callback")
def callback(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    client: Annotated[GoogleClassroomClient, Depends(get_classroom_client)],
    code: Annotated[str | None, Query()] = None,
    state_value: Annotated[str | None, Query(alias="state")] = None,
    error: Annotated[str | None, Query()] = None,
    oauth_cookie: Annotated[str | None, Cookie(alias=OAUTH_COOKIE)] = None,
) -> RedirectResponse:
    if error == "access_denied":
        return _redirect("access_denied")
    if not code or not state_value or not oauth_cookie:
        return _redirect("invalid_state")

    settings = get_settings()
    try:
        verifier = validate_oauth_context(
            oauth_cookie, state_value, user.id, settings.jwt_secret
        )
        tokens = client.exchange_code(code, verifier)
        if not REQUIRED_SCOPES.issubset(tokens.scopes):
            return _redirect("access_blocked")

        existing = ClassroomRepository.get_connection(db, user.id)
        if tokens.refresh_token:
            assert settings.google_token_encryption_key is not None
            encrypted_refresh_token = encrypt_refresh_token(
                tokens.refresh_token, settings.google_token_encryption_key
            )
        elif existing is not None:
            encrypted_refresh_token = existing.encrypted_refresh_token
        else:
            return _redirect("failed")

        ClassroomRepository.upsert_connection(
            db,
            user.id,
            encrypted_refresh_token,
            " ".join(sorted(tokens.scopes)),
        )
        db.commit()
        return _redirect("connected")
    except InvalidOAuthState:
        db.rollback()
        return _redirect("invalid_state")
    except GoogleClassroomError as exception:
        db.rollback()
        target = "access_blocked" if exception.code == "google_access_blocked" else "failed"
        return _redirect(target)
    except ValueError:
        db.rollback()
        return _redirect("failed")


@router.post("/sync", response_model=ClassroomSyncResult)
def sync_classroom(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    client: Annotated[GoogleClassroomClient, Depends(get_classroom_client)],
) -> ClassroomSyncResult:
    settings = get_settings()
    if ClassroomRepository.get_connection(db, user.id) is None:
        raise ApiError(
            status_code=409,
            code="classroom_not_connected",
            message="Conecte o Google Classroom antes de sincronizar.",
        )
    assert settings.google_token_encryption_key is not None
    return ClassroomSyncService().sync(
        db, user.id, client, settings.google_token_encryption_key
    )


@router.delete("/connection", status_code=status.HTTP_204_NO_CONTENT)
def disconnect_classroom(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    connection = ClassroomRepository.get_connection(db, user.id)
    if connection is not None:
        ClassroomRepository.delete_connection(db, connection)
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

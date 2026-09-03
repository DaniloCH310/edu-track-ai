import base64
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

from sqlalchemy import func, select

from app.integrations.google_classroom.client import (
    REQUIRED_SCOPES,
    GoogleTokens,
)
from app.models.subject import Subject
from app.models.task import AcademicTask


class FakeGoogleClient:
    def authorization_url(self, state: str, challenge: str) -> str:
        return f"https://accounts.google.com/o/oauth2/v2/auth?state={state}"

    def exchange_code(self, code: str, verifier: str) -> GoogleTokens:
        assert code == "fake-code"
        assert verifier
        return GoogleTokens(
            access_token="memory-only-access",
            refresh_token="fake-refresh",
            scopes=REQUIRED_SCOPES,
        )

    def refresh_access_token(self, refresh_token: str) -> str:
        assert refresh_token == "fake-refresh"
        return "memory-only-access"

    def list_active_courses(self, access_token: str) -> list[dict]:
        return [{"id": "course-1", "name": "Python", "courseState": "ACTIVE"}]

    def list_published_coursework(self, access_token: str, course_id: str) -> list[dict]:
        return [
            {
                "id": "work-1",
                "title": "Projeto final",
                "dueDate": {"year": 2026, "month": 9, "day": 20},
                "alternateLink": "https://classroom.google.com/c/example",
            }
        ]

    def list_my_submissions(
        self, access_token: str, course_id: str, coursework_id: str
    ) -> list[dict]:
        return [{"id": "submission-1", "state": "CREATED"}]


def authenticate(client):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Ana Estudante",
            "email": "classroom-api@example.com",
            "password": "Senha-Forte-123",
        },
    )
    assert response.status_code == 201
    return response.json()


def configure_classroom(client, monkeypatch):
    import app.api.classroom as classroom_api

    settings = SimpleNamespace(
        google_classroom_enabled=True,
        google_client_id="fake-client-id",
        google_client_secret="fake-client-secret",
        google_oauth_redirect_uri="http://127.0.0.1:8000/api/integrations/classroom/callback",
        google_token_encryption_key=base64.urlsafe_b64encode(b"a" * 32).decode(),
        jwt_secret="test-secret-with-at-least-thirty-two-characters",
        cookie_secure=False,
    )
    monkeypatch.setattr(classroom_api, "get_settings", lambda: settings)
    client.app.dependency_overrides[classroom_api.get_classroom_client] = FakeGoogleClient
    return settings


def connect(client) -> None:
    authorize = client.get(
        "/api/integrations/classroom/authorize", follow_redirects=False
    )
    state = parse_qs(urlparse(authorize.headers["location"]).query)["state"][0]
    callback = client.get(
        f"/api/integrations/classroom/callback?code=fake-code&state={state}",
        follow_redirects=False,
    )
    assert callback.status_code == 307
    assert "classroom=connected" in callback.headers["location"]


def test_classroom_status_requires_edutrack_session(client):
    assert client.get("/api/integrations/classroom").status_code == 401


def test_disabled_integration_returns_available_false(client):
    authenticate(client)

    response = client.get("/api/integrations/classroom")

    assert response.status_code == 200
    assert response.json() == {
        "available": False,
        "connected": False,
        "last_synced_at": None,
        "last_error_code": None,
    }


def test_authorize_sets_http_only_context_cookie_and_redirects(client, monkeypatch):
    authenticate(client)
    configure_classroom(client, monkeypatch)

    response = client.get(
        "/api/integrations/classroom/authorize", follow_redirects=False
    )

    assert response.status_code == 307
    assert response.headers["location"].startswith("https://accounts.google.com/")
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie
    assert "refresh" not in cookie.lower()


def test_callback_rejects_wrong_state_without_storing_token(client, monkeypatch, db_session):
    authenticate(client)
    configure_classroom(client, monkeypatch)
    client.cookies.set("edutrack_google_oauth", "invalid-cookie")

    response = client.get(
        "/api/integrations/classroom/callback?code=fake-code&state=wrong",
        follow_redirects=False,
    )

    assert response.status_code == 307
    assert "classroom=invalid_state" in response.headers["location"]
    assert db_session.scalar(select(func.count()).select_from(Subject)) == 0
    assert "fake-refresh" not in str(response.headers)


def test_connect_sync_and_disconnect_preserve_imported_data(
    client, monkeypatch, db_session
):
    authenticate(client)
    configure_classroom(client, monkeypatch)
    connect(client)

    status = client.get("/api/integrations/classroom")
    sync = client.post("/api/integrations/classroom/sync")
    disconnected = client.delete("/api/integrations/classroom/connection")

    assert status.json()["connected"] is True
    assert sync.status_code == 200
    assert sync.json()["courses_created"] == 1
    assert sync.json()["tasks_created"] == 1
    assert disconnected.status_code == 204
    assert client.get("/api/integrations/classroom").json()["connected"] is False
    assert db_session.scalar(select(func.count()).select_from(Subject)) == 1
    assert db_session.scalar(select(func.count()).select_from(AcademicTask)) == 1
    assert "fake-refresh" not in str(sync.headers) + sync.text

from app.core.security import create_access_token


def test_protected_route_rejects_missing_cookie(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "not_authenticated",
            "message": "Sua sessão não é válida. Entre novamente.",
            "fields": {},
        }
    }


def test_protected_route_rejects_invalid_cookie(client):
    client.cookies.set("edutrack_session", "token-invalido")
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "not_authenticated"


def test_register_sets_secure_browser_cookie(client):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Ana Estudante",
            "email": "ANA@EXAMPLE.COM",
            "password": "Senha-Forte-123",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == "ana@example.com"
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie


def test_login_logout_and_current_user_control_session(client, user_factory):
    user_factory(email="ana@example.com", password="Senha-Forte-123")

    login = client.post(
        "/api/auth/login",
        json={"email": "ANA@example.com", "password": "Senha-Forte-123"},
    )

    assert login.status_code == 200
    assert client.get("/api/auth/me").json()["email"] == "ana@example.com"
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401


def test_login_uses_same_error_for_unknown_and_wrong_password(client, user_factory):
    user_factory(email="ana@example.com", password="Senha-Forte-123")

    unknown = client.post(
        "/api/auth/login",
        json={"email": "ninguem@example.com", "password": "Senha-Forte-123"},
    )
    wrong = client.post(
        "/api/auth/login",
        json={"email": "ana@example.com", "password": "Senha-Errada-456"},
    )

    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()
    assert unknown.json()["error"]["code"] == "invalid_credentials"


def test_duplicate_email_is_case_insensitive(client):
    payload = {
        "name": "Ana Estudante",
        "email": "ana@example.com",
        "password": "Senha-Forte-123",
    }
    assert client.post("/api/auth/register", json=payload).status_code == 201
    payload["email"] = "ANA@EXAMPLE.COM"

    duplicate = client.post("/api/auth/register", json=payload)

    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "email_unavailable"


def test_inactive_and_deleted_users_cannot_authenticate(
    client, user_factory, db_session
):
    inactive = user_factory(email="inativa@example.com", is_active=False)
    login = client.post(
        "/api/auth/login",
        json={"email": inactive.email, "password": "Senha-Forte-123"},
    )
    assert login.status_code == 401

    deleted = user_factory(email="excluida@example.com")
    token = create_access_token(deleted.id)
    db_session.delete(deleted)
    db_session.commit()
    client.cookies.set("edutrack_session", token)

    assert client.get("/api/auth/me").status_code == 401

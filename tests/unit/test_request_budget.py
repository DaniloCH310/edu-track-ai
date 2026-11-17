from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import auth
from app.api.errors import ApiError, register_error_handlers
from app.core.database import get_db
from app.services import request_budget as budgets


def test_windows_expire_and_new_process_starts_empty():
    now = [0]
    budget = budgets.RequestBudget(clock=lambda: now[0])
    budget.consume("login", "peer", ((2, 60),))
    budget.consume("login", "peer", ((2, 60),))
    with pytest.raises(ApiError) as caught:
        budget.consume("login", "peer", ((2, 60),))
    assert caught.value.headers == {"Retry-After": "60"}
    now[0] = 60
    budget.consume("login", "peer", ((2, 60),))
    budgets.RequestBudget().consume("login", "peer", ((1, 60),))


def test_capacity_is_bounded_without_evicting_live_counters():
    now = [0]
    budget = budgets.RequestBudget(clock=lambda: now[0], max_keys=1)
    budget.consume("login", "192.0.2.1", ((1, 60),))
    with pytest.raises(ApiError):
        budget.consume("login", "other", ((1, 60),))
    assert len(budget._buckets) == 1
    assert "192.0.2.1" not in repr(budget._buckets)
    now[0] = 60
    budget.consume("login", "other", ((1, 60),))
    assert len(budget._buckets) == 1


def test_reservation_is_atomic_between_threads():
    budget = budgets.RequestBudget()

    def attempt(_):
        try:
            budget.consume("gemini", "user", ((3, 60),))
            return True
        except ApiError:
            return False

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(attempt, range(20))) == 3


def test_shared_ai_budget_is_per_user_and_persistent_chat_floor_remains(monkeypatch):
    counter = Mock(return_value=0)
    monkeypatch.setattr(budgets.EduAIRepository, "count_student_messages_since", counter)
    settings = SimpleNamespace(edu_ai_requests_per_minute=2, edu_ai_requests_per_day=3)
    user = uuid4()
    budgets.ensure_request_budget(Mock(), user, settings=settings)
    budgets.ensure_request_budget(Mock(), user, settings=settings)
    with pytest.raises(ApiError):
        budgets.ensure_request_budget(Mock(), user, settings=settings)
    budgets.ensure_request_budget(Mock(), uuid4(), settings=settings)
    counter.return_value = 2
    with pytest.raises(ApiError):
        budgets.ensure_request_budget(Mock(), uuid4(), settings=settings)


@pytest.mark.parametrize("operation", ["login", "forgot-password"])
def test_auth_http_limits_success_failure_and_untrusted_headers(monkeypatch, operation):
    monkeypatch.setattr(
        budgets,
        "get_settings",
        lambda: SimpleNamespace(
            auth_login_requests_per_minute=2,
            auth_reset_requests_per_15_minutes=2,
        ),
    )
    app = FastAPI()
    app.include_router(auth.router)
    register_error_handlers(app)
    app.dependency_overrides[get_db] = lambda: Mock()
    user = SimpleNamespace(id=uuid4(), name="Test", email="known@example.com", is_active=True)
    service = Mock(return_value=user if operation == "login" else None)
    monkeypatch.setattr(
        auth.AuthService,
        "authenticate" if operation == "login" else "request_password_reset",
        service,
    )
    monkeypatch.setattr(auth, "set_session_cookie", lambda *args: None)
    payload = {"email": "known@example.com"}
    if operation == "login":
        payload["password"] = "Not-A-Real-Password"
    with TestClient(app, client=("192.0.2.1", 1000)) as first:
        success = first.post(f"/api/auth/{operation}", json=payload)
        assert success.status_code == (200 if operation == "login" else 202)
        if operation == "login":
            service.side_effect = ApiError(401, "invalid_credentials", "Credenciais inválidas.")
        payload["email"] = "absent@example.com"
        failed = first.post(f"/api/auth/{operation}", json=payload)
        assert failed.status_code == (401 if operation == "login" else 202)
        if operation != "login":
            assert failed.json() == success.json()
        denied = first.post(
            f"/api/auth/{operation}",
            json=payload,
            headers={
                "X-Forwarded-For": "203.0.113.1",
                "Forwarded": "for=203.0.113.2",
                "X-Real-IP": "203.0.113.3",
            },
        )
        assert denied.status_code == 429
        assert int(denied.headers["Retry-After"]) > 0
        payload["email"] = "known@example.com"
        assert first.post(f"/api/auth/{operation}", json=payload).json() == denied.json()
        assert "@" not in denied.text
        assert service.call_count == 2
    service.side_effect = None
    with TestClient(app, client=("192.0.2.2", 1000)) as other:
        assert other.post(f"/api/auth/{operation}", json=payload).status_code != 429


def test_day_window_is_not_reset_when_minute_expires():
    now = [0]
    budget = budgets.RequestBudget(clock=lambda: now[0])
    rules = ((1, 60), (2, 86400))
    budget.consume("gemini", "user", rules)
    now[0] = 60
    budget.consume("gemini", "user", rules)
    now[0] = 120
    with pytest.raises(ApiError) as caught:
        budget.consume("gemini", "user", rules)
    assert caught.value.headers == {"Retry-After": str(86400 - 120)}
    now[0] = 86400
    budget.consume("gemini", "user", rules)

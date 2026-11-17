"""Bounded, process-local reservations plus the existing persisted chat budget."""

import hashlib
import hmac
import math
import secrets
import time
from collections import deque
from datetime import UTC, datetime, timedelta
from threading import Lock
from uuid import UUID

from fastapi import Request
from sqlalchemy.orm import Session

from app.api.errors import ApiError
from app.core.config import get_settings
from app.repositories.edu_ia import EduAIRepository


def limited(wait: int) -> ApiError:
    return ApiError(
        429,
        "request_rate_limited",
        "Muitas solicitações. Aguarde e tente novamente.",
        headers={"Retry-After": str(max(1, wait))},
    )


class RequestBudget:
    def __init__(self, *, clock=time.monotonic, max_keys: int = 2048):
        self.clock = clock
        self.max_keys = max_keys
        self._buckets = {}
        self._lock = Lock()
        self._salt = secrets.token_bytes(32)

    def consume(self, scope: str, identity: str, rules: tuple[tuple[int, int], ...]) -> None:
        # Keep neither IP addresses nor user IDs as readable keys; never use account emails.
        key = hmac.digest(self._salt, f"{scope}:{identity}".encode(), hashlib.sha256)
        with self._lock:
            now = self.clock()
            if key not in self._buckets and len(self._buckets) >= self.max_keys:
                self._buckets = {
                    k: (events, ttl)
                    for k, (events, ttl) in self._buckets.items()
                    if events and events[-1] + ttl > now
                }
                if len(self._buckets) >= self.max_keys:
                    wait = min(events[-1] + ttl - now for events, ttl in self._buckets.values())
                    raise limited(math.ceil(wait))  # Do not evict live counters to admit new keys.
            events, _ = self._buckets.get(key, (deque(), 0))
            ttl = max(window for _, window in rules)
            while events and events[0] <= now - ttl:
                events.popleft()
            waits = []
            for limit, window in rules:
                recent = [stamp for stamp in events if stamp > now - window]
                if len(recent) >= limit:
                    waits.append(math.ceil(recent[-limit] + window - now))
            if waits:
                raise limited(max(waits))
            events.append(now)
            self._buckets[key] = (events, ttl)


_process_budget = RequestBudget()


def get_request_budget() -> RequestBudget:
    return _process_budget


def ensure_auth_budget(request: Request, operation: str) -> None:
    settings = get_settings()
    origin = request.client.host if request.client else "unknown-peer"
    if operation == "login":
        rules = ((settings.auth_login_requests_per_minute, 60),)
    else:
        rules = ((settings.auth_reset_requests_per_15_minutes, 900),)
    get_request_budget().consume(operation, origin, rules)


def ensure_request_budget(db: Session, user_id: UUID, *, settings=None) -> None:
    settings = settings or get_settings()
    now = datetime.now(UTC)
    # Preserve the old persistent floor for chat, including across process restarts.
    for limit, window in (
        (settings.edu_ai_requests_per_minute, 60),
        (settings.edu_ai_requests_per_day, 86400),
    ):
        if (
            EduAIRepository.count_student_messages_since(
                db, user_id, now - timedelta(seconds=window)
            )
            >= limit
        ):
            raise limited(window)
    # Reserve BEFORE external work; failures also consume budget and cannot race locally.
    get_request_budget().consume(
        "gemini",
        str(user_id),
        (
            (settings.edu_ai_requests_per_minute, 60),
            (settings.edu_ai_requests_per_day, 86400),
        ),
    )

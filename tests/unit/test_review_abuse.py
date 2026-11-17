from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from threading import Event, Lock
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import OperationalError

from app.api import review_missions as api
from app.api.errors import ApiError
from app.integrations.edu_ia.gemini import GeminiError
from app.models.review_mission import ReviewMissionStatus as Status
from app.repositories.review_missions import ReviewMissionRepository
from app.schemas.review_mission import ReviewMissionSubmission


@pytest.fixture
def review(monkeypatch):
    mission = SimpleNamespace(
        id=uuid4(),
        status=Status.IN_PROGRESS,
        due_date=date.today(),
        questions=["One?", "Two?", "Three?"],
        answers=[],
        mastery_percent=None,
        mastery_summary=None,
        completed_at=None,
    )
    task = SimpleNamespace(id=uuid4(), title="Task", description="Context")
    subject = SimpleNamespace(id=uuid4(), name="Subject", description="Context")
    item = (mission, task, subject)
    lookup = Mock(return_value=item)
    monkeypatch.setattr(ReviewMissionRepository, "get_for_user", lookup)
    client = Mock()
    client.generate_reply.return_value = '{"mastery_percent":80,"mastery_summary":"Good"}'
    monkeypatch.setattr(api, "edu_ai_client", lambda: client)
    budget = Mock()
    monkeypatch.setattr(api, "ensure_request_budget", budget)
    return SimpleNamespace(
        mission=mission,
        item=item,
        lookup=lookup,
        client=client,
        budget=budget,
        db=Mock(),
        user=SimpleNamespace(id=uuid4()),
        data=ReviewMissionSubmission(answers=["First", "Second", "Third"]),
    )


def submit(s):
    return api.submit_review_mission(s.mission.id, s.data, s.user, s.db)


def test_repeat_submission_and_start_preserve_completed_assessment(review):
    s = review
    first = submit(s)
    s.data = ReviewMissionSubmission(answers=["Changed", "Changed", "Changed"])
    assert submit(s) == first
    assert api.start_review_mission(s.mission.id, s.user, s.db) == first
    assert s.mission.answers == ["First", "Second", "Third"]
    s.client.generate_reply.assert_called_once()
    s.budget.assert_called_once_with(s.db, s.user.id)
    s.lookup.assert_called_with(s.db, s.mission.id, s.user.id, lock=True)


@pytest.mark.parametrize("failure", [GeminiError("unavailable"), ValueError("bad response")])
def test_provider_failure_preserves_answers_without_fake_score(review, failure):
    s = review
    s.client.generate_reply.side_effect = failure
    result = submit(s)
    assert result.status == Status.COMPLETED
    assert result.mastery_percent is None
    assert "ainda não foi avaliado" in result.mastery_summary
    assert s.mission.answers == s.data.answers
    s.db.commit.assert_called_once()
    submit(s)
    s.client.generate_reply.assert_called_once()


@pytest.mark.parametrize("condition", ["pending", "future", "unowned", "budget"])
def test_invalid_state_ownership_or_budget_prevents_external_work(review, condition):
    s = review
    if condition == "pending":
        s.mission.status = Status.PENDING
    elif condition == "future":
        s.mission.due_date = date.today() + timedelta(days=1)
    elif condition == "unowned":
        s.lookup.return_value = None
    else:
        s.budget.side_effect = ApiError(429, "limited", "Wait")
    with pytest.raises(ApiError):
        submit(s)
    s.client.generate_reply.assert_not_called()
    s.db.commit.assert_not_called()
    assert s.mission.answers == []


def test_start_reuses_existing_questions_without_consuming_budget(review):
    s = review
    api.start_review_mission(s.mission.id, s.user, s.db)
    s.client.generate_reply.assert_not_called()
    s.budget.assert_not_called()


@pytest.mark.parametrize("configured", [True, False])
def test_start_reserves_only_once_and_offline_fallback_is_free(review, monkeypatch, configured):
    s = review
    s.mission.status = Status.PENDING
    s.mission.questions = []
    if not configured:
        monkeypatch.setattr(api, "edu_ai_client", lambda: None)
    first = api.start_review_mission(s.mission.id, s.user, s.db)
    second = api.start_review_mission(s.mission.id, s.user, s.db)
    assert first.questions == second.questions
    assert len(first.questions) == 3
    assert s.budget.call_count == int(configured)
    assert s.client.generate_reply.call_count == int(configured)


def test_pg_query_locks_only_owned_review_and_refreshes_identity_map():
    db = Mock()
    ReviewMissionRepository.get_for_user(db, uuid4(), uuid4(), lock=True)
    statement = db.execute.call_args.args[0]
    sql = str(statement.compile(dialect=postgresql.dialect()))
    assert "FOR UPDATE OF review_missions NOWAIT" in sql
    assert "subjects.user_id =" in sql
    assert "academic_tasks.subject_id = subjects.id" in sql
    assert statement.get_execution_options()["populate_existing"] is True


def test_concurrent_submission_simulated_database_lock(review):
    s = review
    lock = Lock()
    entered, release = Event(), Event()

    def lookup(*args, **kwargs):
        if not lock.acquire(blocking=False):
            original = Exception("locked")
            original.sqlstate = "55P03"
            raise OperationalError("", {}, original)
        return s.item

    s.lookup.side_effect = lookup

    def generate(*args):
        entered.set()
        assert release.wait(5)
        return '{"mastery_percent":80,"mastery_summary":"Good"}'

    s.client.generate_reply.side_effect = generate
    s.db.commit.side_effect = lock.release
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(submit, s)
        assert entered.wait(5)
        try:
            with pytest.raises(ApiError) as caught:
                submit(s)
            assert caught.value.status_code == 409
            assert caught.value.headers == {"Retry-After": "1"}
        finally:
            release.set()
        assert first.result().status == Status.COMPLETED
    s.client.generate_reply.assert_called_once()

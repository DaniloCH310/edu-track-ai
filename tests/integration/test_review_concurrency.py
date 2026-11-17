"""Real PostgreSQL transactions, exclusively in the disposable GitHub Actions service."""

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime
from threading import Event, Lock
from types import SimpleNamespace

import pytest
from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from app.api import review_missions as api
from app.api.errors import ApiError
from app.core.database import SessionLocal
from app.integrations.edu_ia.gemini import GeminiError
from app.models.review_mission import ReviewMission, ReviewMissionStatus
from app.models.subject import Subject
from app.models.task import AcademicTask, TaskStatus
from app.schemas.review_mission import ReviewMissionSubmission

pytestmark = pytest.mark.skipif(
    os.environ.get("GITHUB_ACTIONS") != "true",
    reason="Runs only against the P1-authorized disposable PostgreSQL CI service",
)


@pytest.fixture
def mission_ids(db_session, user_factory):
    # These fixtures perform the P1 checks before any setup/cleanup SQL.
    owner = user_factory(email="review-owner@example.com")
    other = user_factory(email="review-other@example.com")
    subject = Subject(user_id=owner.id, name="Review concurrency", workload_hours=30)
    db_session.add(subject)
    db_session.flush()
    task = AcademicTask(
        subject_id=subject.id,
        title="Concurrency",
        due_date=date.today(),
        status=TaskStatus.COMPLETED,
        completed_at=datetime.now(UTC),
    )
    db_session.add(task)
    db_session.flush()
    mission = ReviewMission(
        task_id=task.id,
        subject_id=subject.id,
        due_date=date.today(),
        status=ReviewMissionStatus.IN_PROGRESS,
        questions=["One?", "Two?", "Three?"],
    )
    db_session.add(mission)
    db_session.commit()
    return mission.id, owner.id, other.id


def submit(mission_id, user_id, answers=None):
    with SessionLocal() as db:
        return api.submit_review_mission(
            mission_id,
            ReviewMissionSubmission(answers=answers or ["One", "Two", "Three"]),
            SimpleNamespace(id=user_id),
            db,
        )


def snapshot(mission_id):
    with SessionLocal() as db:
        mission = db.get(ReviewMission, mission_id)
        return (
            mission.status,
            mission.answers,
            mission.mastery_percent,
            mission.mastery_summary,
            mission.completed_at,
        )


def test_postgres_simultaneous_submissions_have_one_evaluation(monkeypatch, mission_ids):
    mission_id, owner_id, other_id = mission_ids
    entered, release = Event(), Event()
    calls = []
    mutex = Lock()

    class FakeGemini:
        def generate_reply(self, *args):
            with mutex:
                calls.append(1)
            entered.set()
            assert release.wait(10), "The test must release the simulated provider"
            return '{"mastery_percent":85,"mastery_summary":"Understands the concepts"}'

    monkeypatch.setattr(api, "edu_ai_client", lambda: FakeGemini())
    initial = snapshot(mission_id)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(submit, mission_id, owner_id)
        try:
            assert entered.wait(5), "First submission did not reach the fake provider"
            # While Gemini is paused, no assessment is partially visible to other sessions.
            assert snapshot(mission_id) == initial
            # Prove that the row remains locked during the external wait.
            with SessionLocal() as observer:
                with pytest.raises(OperationalError) as locked:
                    observer.execute(
                        select(ReviewMission)
                        .where(ReviewMission.id == mission_id)
                        .with_for_update(nowait=True)
                    )
                assert locked.value.orig.sqlstate == "55P03"
                observer.rollback()
            second = pool.submit(submit, mission_id, owner_id)
            with pytest.raises(ApiError) as busy:
                second.result(timeout=2)
            assert busy.value.status_code == 409
            assert busy.value.headers == {"Retry-After": "1"}
            with pytest.raises(ApiError) as denied:
                submit(mission_id, other_id)
            assert denied.value.status_code == 404
        finally:
            release.set()
        result = first.result(timeout=5)
    assert result.mastery_percent == 85
    assert len(calls) == 1
    saved = snapshot(mission_id)
    assert saved[0] == ReviewMissionStatus.COMPLETED
    assert saved[1] == ["One", "Two", "Three"]
    assert saved[4] is not None
    assert submit(mission_id, owner_id, ["Changed"] * 3) == result
    assert snapshot(mission_id) == saved
    assert len(calls) == 1
    # Commit released the lock, including for a fresh independent connection.
    with SessionLocal() as observer:
        observer.execute(
            select(ReviewMission).where(ReviewMission.id == mission_id).with_for_update(nowait=True)
        )


def test_postgres_provider_failure_saves_answers_without_fictional_score(monkeypatch, mission_ids):
    mission_id, owner_id, _ = mission_ids
    calls = []

    class UnavailableGemini:
        def generate_reply(self, *args):
            calls.append(1)
            raise GeminiError("edu_ai_temporarily_unavailable")

    monkeypatch.setattr(api, "edu_ai_client", lambda: UnavailableGemini())
    result = submit(mission_id, owner_id)
    assert result.status == ReviewMissionStatus.COMPLETED
    assert result.mastery_percent is None
    assert "ainda não foi avaliado" in result.mastery_summary
    assert snapshot(mission_id)[1] == ["One", "Two", "Three"]
    assert submit(mission_id, owner_id) == result
    assert len(calls) == 1


def test_postgres_failed_commit_rolls_back_entire_assessment(monkeypatch, mission_ids):
    mission_id, owner_id, _ = mission_ids

    class FakeGemini:
        def generate_reply(self, *args):
            return '{"mastery_percent":90,"mastery_summary":"Good"}'

    monkeypatch.setattr(api, "edu_ai_client", lambda: FakeGemini())
    initial = snapshot(mission_id)
    with SessionLocal() as db:

        def fail_commit():
            db.flush()  # Actually write inside the transaction before simulating failure.
            raise RuntimeError("simulated commit failure")

        monkeypatch.setattr(db, "commit", fail_commit)
        with pytest.raises(RuntimeError, match="simulated commit failure"):
            api.submit_review_mission(
                mission_id,
                ReviewMissionSubmission(answers=["A"] * 3),
                SimpleNamespace(id=owner_id),
                db,
            )
    assert snapshot(mission_id) == initial
    assert submit(mission_id, owner_id).mastery_percent == 90

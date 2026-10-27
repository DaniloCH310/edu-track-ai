from datetime import date, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.review_mission import ReviewMission, ReviewMissionStatus
from app.models.subject import Subject
from app.models.task import AcademicTask, TaskStatus

STUDENT_TIMEZONE = ZoneInfo("America/Sao_Paulo")


def review_due_date(completed_at: datetime) -> date:
    """Schedule spaced review from the student's calendar day, not the UTC rollover."""
    return completed_at.astimezone(STUDENT_TIMEZONE).date() + timedelta(days=3)


class ReviewMissionRepository:
    @staticmethod
    def backfill_completed_tasks(db: Session, tasks: list[AcademicTask]) -> bool:
        """Schedule reviews for tasks completed before this feature was released."""
        completed = [
            task
            for task in tasks
            if task.status == TaskStatus.COMPLETED and task.completed_at is not None
        ]
        if not completed:
            return False
        # A versão inicial não deve transformar todo o histórico em uma fila
        # impossível de recuperar. O retroativo começa pela vitória mais recente;
        # as próximas conclusões sempre recebem sua própria missão.
        completed = [max(completed, key=lambda task: task.completed_at)]

        existing_task_ids = set(
            db.scalars(
                select(ReviewMission.task_id).where(
                    ReviewMission.task_id.in_([task.id for task in completed])
                )
            )
        )
        created = False
        for task in completed:
            if task.id in existing_task_ids:
                continue
            scheduled_for = review_due_date(task.completed_at)
            db.add(
                ReviewMission(
                    task_id=task.id,
                    subject_id=task.subject_id,
                    due_date=scheduled_for,
                )
            )
            created = True
        return created

    @staticmethod
    def sync_for_task(db: Session, task: AcademicTask) -> None:
        mission = db.scalar(select(ReviewMission).where(ReviewMission.task_id == task.id))
        if task.status != TaskStatus.COMPLETED:
            if mission is not None and mission.status != ReviewMissionStatus.COMPLETED:
                db.delete(mission)
            return

        completed_at = task.completed_at
        if completed_at is None:
            return
        scheduled_for = review_due_date(completed_at)
        if mission is None:
            db.add(
                ReviewMission(
                    task_id=task.id,
                    subject_id=task.subject_id,
                    due_date=scheduled_for,
                )
            )
        elif mission.status != ReviewMissionStatus.COMPLETED:
            mission.due_date = scheduled_for
            mission.status = ReviewMissionStatus.PENDING
            mission.questions = []
            mission.answers = []
            mission.mastery_percent = None
            mission.mastery_summary = None
            mission.completed_at = None

    @staticmethod
    def list_for_user(
        db: Session, user_id: UUID
    ) -> list[tuple[ReviewMission, AcademicTask, Subject]]:
        statement = (
            select(ReviewMission, AcademicTask, Subject)
            .join(AcademicTask, ReviewMission.task_id == AcademicTask.id)
            .join(Subject, ReviewMission.subject_id == Subject.id)
            .where(Subject.user_id == user_id)
            .order_by(ReviewMission.due_date.asc(), ReviewMission.created_at.asc())
        )
        return list(db.execute(statement).all())

    @staticmethod
    def get_for_user(
        db: Session, mission_id: UUID, user_id: UUID
    ) -> tuple[ReviewMission, AcademicTask, Subject] | None:
        statement = (
            select(ReviewMission, AcademicTask, Subject)
            .join(AcademicTask, ReviewMission.task_id == AcademicTask.id)
            .join(Subject, ReviewMission.subject_id == Subject.id)
            .where(ReviewMission.id == mission_id, Subject.user_id == user_id)
        )
        return db.execute(statement).one_or_none()

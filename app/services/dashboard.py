from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AcademicTask, Subject, TaskStatus
from app.repositories.review_missions import ReviewMissionRepository
from app.schemas.dashboard import (
    DashboardOutput,
    StudyRecommendationOutput,
    SubjectProgressOutput,
    UpcomingTaskOutput,
)
from app.schemas.review_mission import ReviewMissionOutput
from app.services.review_missions import is_available


def percentage(completed: int, total: int) -> int:
    return round(completed / total * 100) if total else 0


def recommendation_reason(
    task: AcademicTask, progress: int, today: date, available_minutes: int
) -> tuple[str, str, str]:
    time_copy = f"Você tem {available_minutes} minutos"
    estimated_minutes = task.estimated_minutes or 30
    if task.due_date < today:
        return (
            "urgent",
            f"{time_copy}: esta tarefa está atrasada; avance agora para retomar seu ritmo.",
            "task",
        )
    if task.due_date == today:
        return "urgent", f"{time_copy}: esta entrega vence hoje.", "task"
    if estimated_minutes > available_minutes:
        return (
            "attention",
            f"{time_copy}: faça uma revisão guiada antes de avançar nesta missão de "
            f"{estimated_minutes} minutos.",
            "edu_ai",
        )
    if task.due_date <= today + timedelta(days=3):
        days = (task.due_date - today).days
        return (
            "attention",
            f"{time_copy}: avance antes do prazo em {days} dias.",
            "task",
        )
    return (
        "routine",
        f"{time_copy}: este é um passo viável para fortalecer uma disciplina com "
        f"{progress}% de progresso.",
        "task",
    )


def calculate_dashboard(
    subjects: list[Subject],
    tasks: list[AcademicTask],
    today: date,
    review_missions: list[ReviewMissionOutput] | None = None,
    available_minutes: int = 25,
) -> DashboardOutput:
    subject_by_id = {subject.id: subject for subject in subjects}
    completed_tasks = sum(task.status == TaskStatus.COMPLETED for task in tasks)
    pending_tasks = [task for task in tasks if task.status != TaskStatus.COMPLETED]

    progress_items: list[SubjectProgressOutput] = []
    for subject in sorted(subjects, key=lambda item: item.name.casefold()):
        subject_tasks = [task for task in tasks if task.subject_id == subject.id]
        subject_completed = sum(task.status == TaskStatus.COMPLETED for task in subject_tasks)
        progress_items.append(
            SubjectProgressOutput(
                subject_id=subject.id,
                subject_name=subject.name,
                color=subject.color or "#6750A4",
                progress=percentage(subject_completed, len(subject_tasks)),
                completed_tasks=subject_completed,
                total_tasks=len(subject_tasks),
            )
        )

    upcoming = []
    for task in sorted(pending_tasks, key=lambda item: (item.due_date, item.title.casefold()))[:4]:
        subject = subject_by_id[task.subject_id]
        upcoming.append(
            UpcomingTaskOutput(
                id=task.id,
                subject_id=task.subject_id,
                subject_name=subject.name,
                title=task.title,
                due_date=task.due_date,
                status=task.status,
            )
        )

    progress_by_subject_id = {item.subject_id: item.progress for item in progress_items}
    recommendation = None
    if pending_tasks:

        def priority_key(
            task: AcademicTask,
        ) -> tuple[int, int, int, int, int, date, str]:
            if task.due_date < today:
                urgency = 0
            elif task.due_date == today:
                urgency = 1
            elif task.due_date <= today + timedelta(days=3):
                urgency = 2
            else:
                urgency = 3
            estimated_minutes = task.estimated_minutes or 30
            difficulty = task.difficulty or 3
            time_overflow = max(estimated_minutes - available_minutes, 0)
            difficulty_penalty = difficulty if available_minutes < 30 else 0
            return (
                urgency,
                0 if time_overflow == 0 else 1,
                time_overflow,
                difficulty_penalty,
                progress_by_subject_id[task.subject_id],
                task.due_date,
                task.title.casefold(),
            )

        task = min(pending_tasks, key=priority_key)
        priority, reason, action_type = recommendation_reason(
            task,
            progress_by_subject_id[task.subject_id],
            today,
            available_minutes,
        )
        difficulty = task.difficulty or 3
        estimated_minutes = task.estimated_minutes or 30
        recommendation = StudyRecommendationOutput(
            id=task.id,
            subject_id=task.subject_id,
            subject_name=subject_by_id[task.subject_id].name,
            title=task.title,
            due_date=task.due_date,
            status=task.status,
            priority=priority,
            reason=reason,
            difficulty=difficulty,
            estimated_minutes=estimated_minutes,
            action_type=action_type,
        )

    return DashboardOutput(
        total_subjects=len(subjects),
        total_tasks=len(tasks),
        completed_tasks=completed_tasks,
        overall_progress=percentage(completed_tasks, len(tasks)),
        due_soon=sum(today <= task.due_date <= today + timedelta(days=3) for task in pending_tasks),
        overdue=sum(task.due_date < today for task in pending_tasks),
        progress_by_subject=progress_items,
        upcoming=upcoming,
        recommended_task=recommendation,
        review_missions=review_missions or [],
    )


class DashboardService:
    @staticmethod
    def build(
        db: Session, user_id: UUID, today: date, available_minutes: int = 25
    ) -> DashboardOutput:
        subjects = list(db.scalars(select(Subject).where(Subject.user_id == user_id)))
        tasks = list(
            db.scalars(select(AcademicTask).join(Subject).where(Subject.user_id == user_id))
        )
        if ReviewMissionRepository.backfill_completed_tasks(db, tasks):
            db.commit()
        reviews = [
            ReviewMissionOutput(
                id=mission.id,
                task_id=task.id,
                subject_id=subject.id,
                task_title=task.title,
                subject_name=subject.name,
                due_date=mission.due_date,
                status=mission.status,
                is_available=is_available(mission, today),
                questions=mission.questions,
                mastery_percent=mission.mastery_percent,
                mastery_summary=mission.mastery_summary,
                completed_at=mission.completed_at,
            )
            for mission, task, subject in ReviewMissionRepository.list_for_user(db, user_id)
        ]
        return calculate_dashboard(subjects, tasks, today, reviews, available_minutes)

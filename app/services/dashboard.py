from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AcademicTask, Subject, TaskStatus
from app.schemas.dashboard import (
    DashboardOutput,
    StudyRecommendationOutput,
    SubjectProgressOutput,
    UpcomingTaskOutput,
)


def percentage(completed: int, total: int) -> int:
    return round(completed / total * 100) if total else 0


def recommendation_reason(task: AcademicTask, progress: int, today: date) -> tuple[str, str]:
    if task.due_date < today:
        return "urgent", "Esta tarefa está atrasada: conclua-a para retomar seu ritmo."
    if task.due_date == today:
        return "urgent", "Esta tarefa vence hoje: ela é sua prioridade do dia."
    if task.due_date <= today + timedelta(days=3):
        days = (task.due_date - today).days
        return (
            "attention",
            f"Esta tarefa vence em {days} dias: adiante-se para não acumular entregas.",
        )
    return "routine", f"Esta disciplina está com {progress}% de progresso: avance por aqui."


def calculate_dashboard(
    subjects: list[Subject], tasks: list[AcademicTask], today: date
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

        def priority_key(task: AcademicTask) -> tuple[int, int, date, str]:
            if task.due_date < today:
                urgency = 0
            elif task.due_date == today:
                urgency = 1
            elif task.due_date <= today + timedelta(days=3):
                urgency = 2
            else:
                urgency = 3
            return (
                urgency,
                progress_by_subject_id[task.subject_id],
                task.due_date,
                task.title.casefold(),
            )

        task = min(pending_tasks, key=priority_key)
        priority, reason = recommendation_reason(
            task, progress_by_subject_id[task.subject_id], today
        )
        recommendation = StudyRecommendationOutput(
            id=task.id,
            subject_id=task.subject_id,
            subject_name=subject_by_id[task.subject_id].name,
            title=task.title,
            due_date=task.due_date,
            status=task.status,
            priority=priority,
            reason=reason,
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
    )


class DashboardService:
    @staticmethod
    def build(db: Session, user_id: UUID, today: date) -> DashboardOutput:
        subjects = list(db.scalars(select(Subject).where(Subject.user_id == user_id)))
        tasks = list(
            db.scalars(select(AcademicTask).join(Subject).where(Subject.user_id == user_id))
        )
        return calculate_dashboard(subjects, tasks, today)

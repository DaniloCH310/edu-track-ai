from datetime import date
from uuid import UUID

from pydantic import BaseModel

from app.models import TaskStatus


class SubjectProgressOutput(BaseModel):
    subject_id: UUID
    subject_name: str
    color: str
    progress: int
    completed_tasks: int
    total_tasks: int


class UpcomingTaskOutput(BaseModel):
    id: UUID | None
    subject_id: UUID
    subject_name: str
    title: str
    due_date: date
    status: TaskStatus


class StudyRecommendationOutput(UpcomingTaskOutput):
    priority: str
    reason: str


class DashboardOutput(BaseModel):
    total_subjects: int
    total_tasks: int
    completed_tasks: int
    overall_progress: int
    due_soon: int
    overdue: int
    progress_by_subject: list[SubjectProgressOutput]
    upcoming: list[UpcomingTaskOutput]
    recommended_task: StudyRecommendationOutput | None

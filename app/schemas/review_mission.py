from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.review_mission import ReviewMissionStatus


class ReviewMissionOutput(BaseModel):
    id: UUID
    task_id: UUID
    subject_id: UUID
    task_title: str
    subject_name: str
    due_date: date
    status: ReviewMissionStatus
    is_available: bool
    questions: list[str] = []
    mastery_percent: int | None = None
    mastery_summary: str | None = None
    completed_at: datetime | None = None


class ReviewMissionSubmission(BaseModel):
    answers: list[str] = Field(min_length=3, max_length=3)

    @field_validator("answers")
    @classmethod
    def answers_need_content(cls, answers: list[str]) -> list[str]:
        cleaned = [answer.strip() for answer in answers]
        if any(not answer for answer in cleaned):
            raise ValueError("Responda às três perguntas antes de concluir a missão.")
        return cleaned

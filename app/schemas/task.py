from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import TaskStatus


class TaskFields(BaseModel):
    subject_id: UUID
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    due_date: date
    status: TaskStatus = TaskStatus.PENDING

    @field_validator("title", mode="before")
    @classmethod
    def trim_title(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("description", mode="before")
    @classmethod
    def trim_description(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        trimmed = value.strip()
        return trimmed or None


class TaskCreate(TaskFields):
    pass


class TaskUpdate(TaskFields):
    pass


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class TaskOutput(TaskFields):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subject_name: str | None = None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


TaskOrder = Literal["due_asc", "due_desc", "created_desc"]

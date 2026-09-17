from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.edu_ia import EduAIMessageRole


class EduAIStatus(BaseModel):
    available: bool


class EduAIConversationCreate(BaseModel):
    subject_id: UUID | None = None
    task_id: UUID | None = None


class EduAIMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)

    @field_validator("content", mode="before")
    @classmethod
    def trim_content(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class EduAIMessageOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: EduAIMessageRole
    content: str
    created_at: datetime


class EduAIConversationOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    subject_id: UUID | None
    task_id: UUID | None
    created_at: datetime
    updated_at: datetime


class EduAIConversationDetail(EduAIConversationOutput):
    messages: list[EduAIMessageOutput]

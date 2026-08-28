from datetime import date, datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SubjectFields(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    professor: str | None = Field(default=None, max_length=160)
    workload_hours: int = Field(gt=0, le=10000)
    description: str | None = Field(default=None, max_length=4000)
    period: str | None = Field(default=None, max_length=40)
    color: str = Field(default="#6750A4", pattern=r"^#[0-9A-Fa-f]{6}$")
    start_date: date | None = None
    end_date: date | None = None

    @field_validator("name", mode="before")
    @classmethod
    def trim_name(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("professor", "description", "period", mode="before")
    @classmethod
    def trim_optional_text(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        trimmed = value.strip()
        return trimmed or None

    @field_validator("color")
    @classmethod
    def normalize_color(cls, value: str) -> str:
        return value.upper()

    @model_validator(mode="after")
    def validate_date_range(self) -> Self:
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("A data final não pode ser anterior à data inicial.")
        return self


class SubjectCreate(SubjectFields):
    pass


class SubjectUpdate(SubjectFields):
    pass


class SubjectOutput(SubjectFields):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    progress: int = 0
    created_at: datetime
    updated_at: datetime


class SubjectOption(BaseModel):
    id: UUID
    name: str

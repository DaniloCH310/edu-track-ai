from datetime import datetime

from pydantic import BaseModel, Field


class ClassroomSyncResult(BaseModel):
    courses_created: int = 0
    courses_updated: int = 0
    tasks_created: int = 0
    tasks_updated: int = 0
    skipped_without_due_date: int = 0
    warnings: list[str] = Field(default_factory=list)


class ClassroomStatus(BaseModel):
    available: bool
    connected: bool
    last_synced_at: datetime | None = None
    last_error_code: str | None = None

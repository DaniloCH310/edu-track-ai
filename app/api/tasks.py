from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.api.errors import ApiError
from app.core.database import get_db
from app.models.task import AcademicTask, TaskStatus
from app.repositories.subjects import SubjectRepository
from app.repositories.tasks import TaskRepository
from app.schemas.task import (
    TaskCreate,
    TaskOrder,
    TaskOutput,
    TaskStatusUpdate,
    TaskUpdate,
)

router = APIRouter(prefix="/api/tasks", tags=["tarefas"])


def task_not_found() -> ApiError:
    return ApiError(404, "task_not_found", "Tarefa não encontrada.")


def get_owned_task(db: Session, task_id: UUID, user_id: UUID) -> AcademicTask:
    task = TaskRepository.get_for_user(db, task_id, user_id)
    if task is None:
        raise task_not_found()
    return task


def ensure_owned_subject(db: Session, subject_id: UUID, user_id: UUID) -> None:
    if SubjectRepository.get_for_user(db, subject_id, user_id) is None:
        raise ApiError(404, "subject_not_found", "Disciplina não encontrada.")


@router.get("", response_model=list[TaskOutput])
def list_tasks(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    query: str | None = None,
    task_status: Annotated[TaskStatus | None, Query(alias="status")] = None,
    subject_id: UUID | None = None,
    order: TaskOrder = "due_asc",
) -> list[AcademicTask]:
    return TaskRepository.list_for_user(
        db,
        user.id,
        query=query,
        status=task_status,
        subject_id=subject_id,
        order=order,
    )


@router.post("", response_model=TaskOutput, status_code=status.HTTP_201_CREATED)
def create_task(
    data: TaskCreate,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> AcademicTask:
    ensure_owned_subject(db, data.subject_id, user.id)
    return TaskRepository.create(db, data)


@router.get("/{task_id}", response_model=TaskOutput)
def get_task(
    task_id: UUID,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> AcademicTask:
    return get_owned_task(db, task_id, user.id)


@router.put("/{task_id}", response_model=TaskOutput)
def update_task(
    task_id: UUID,
    data: TaskUpdate,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> AcademicTask:
    task = get_owned_task(db, task_id, user.id)
    ensure_owned_subject(db, data.subject_id, user.id)
    return TaskRepository.update(db, task, data)


@router.patch("/{task_id}/status", response_model=TaskOutput)
def update_task_status(
    task_id: UUID,
    data: TaskStatusUpdate,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> AcademicTask:
    task = get_owned_task(db, task_id, user.id)
    return TaskRepository.update_status(db, task, data.status)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: UUID,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    task = get_owned_task(db, task_id, user.id)
    TaskRepository.delete(db, task)

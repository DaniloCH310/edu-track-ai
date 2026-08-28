from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.api.errors import ApiError
from app.core.database import get_db
from app.models.subject import Subject
from app.repositories.subjects import SubjectRepository
from app.schemas.subject import SubjectCreate, SubjectOutput, SubjectUpdate

router = APIRouter(prefix="/api/subjects", tags=["disciplinas"])


def get_owned_subject(db: Session, subject_id: UUID, user_id: UUID) -> Subject:
    subject = SubjectRepository.get_for_user(db, subject_id, user_id)
    if subject is None:
        raise ApiError(
            status_code=404,
            code="subject_not_found",
            message="Disciplina não encontrada.",
        )
    return subject


@router.get("", response_model=list[SubjectOutput])
def list_subjects(
    user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> list[Subject]:
    return SubjectRepository.list_for_user(db, user.id)


@router.post("", response_model=SubjectOutput, status_code=status.HTTP_201_CREATED)
def create_subject(
    data: SubjectCreate,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Subject:
    return SubjectRepository.create(db, user.id, data)


@router.get("/{subject_id}", response_model=SubjectOutput)
def get_subject(
    subject_id: UUID,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Subject:
    return get_owned_subject(db, subject_id, user.id)


@router.put("/{subject_id}", response_model=SubjectOutput)
def update_subject(
    subject_id: UUID,
    data: SubjectUpdate,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Subject:
    subject = get_owned_subject(db, subject_id, user.id)
    return SubjectRepository.update(db, subject, data)


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(
    subject_id: UUID,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    subject = get_owned_subject(db, subject_id, user.id)
    SubjectRepository.delete(db, subject)

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.api.errors import ApiError
from app.core.config import get_settings
from app.core.database import get_db
from app.integrations.edu_ia.gemini import GeminiClient
from app.repositories.review_missions import ReviewMissionRepository
from app.schemas.review_mission import ReviewMissionOutput, ReviewMissionSubmission
from app.services.review_missions import assess_answers, create_questions, is_available

router = APIRouter(prefix="/api/reviews", tags=["missões de revisão"])


def output(item, today: date) -> ReviewMissionOutput:
    mission, task, subject = item
    return ReviewMissionOutput(
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


def get_owned_mission(db: Session, mission_id: UUID, user_id: UUID):
    item = ReviewMissionRepository.get_for_user(db, mission_id, user_id)
    if item is None:
        raise ApiError(404, "review_mission_not_found", "Missão de revisão não encontrada.")
    return item


def edu_ai_client() -> GeminiClient | None:
    settings = get_settings()
    if not settings.edu_ai_enabled or not settings.gemini_api_key:
        return None
    return GeminiClient(settings.gemini_api_key, settings.gemini_model)


@router.get("", response_model=list[ReviewMissionOutput])
def list_review_missions(
    user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> list[ReviewMissionOutput]:
    today = date.today()
    return [output(item, today) for item in ReviewMissionRepository.list_for_user(db, user.id)]


@router.post("/{mission_id}/start", response_model=ReviewMissionOutput)
def start_review_mission(
    mission_id: UUID,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> ReviewMissionOutput:
    item = get_owned_mission(db, mission_id, user.id)
    mission, task, subject = item
    if not is_available(mission, date.today()):
        raise ApiError(
            409,
            "review_mission_not_available",
            "Esta revisão estará disponível na data programada.",
        )
    create_questions(mission, task, subject, edu_ai_client())
    db.commit()
    db.refresh(mission)
    return output((mission, task, subject), date.today())


@router.post("/{mission_id}/submit", response_model=ReviewMissionOutput)
def submit_review_mission(
    mission_id: UUID,
    data: ReviewMissionSubmission,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> ReviewMissionOutput:
    item = get_owned_mission(db, mission_id, user.id)
    mission, task, subject = item
    if not mission.questions:
        raise ApiError(
            409,
            "review_mission_not_started",
            "Inicie a revisão antes de enviar as respostas.",
        )
    assess_answers(mission, task, subject, data.answers, edu_ai_client())
    db.commit()
    db.refresh(mission)
    return output((mission, task, subject), date.today())

from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.api.errors import ApiError
from app.core.config import get_settings
from app.core.database import get_db
from app.integrations.edu_ia.gemini import GeminiClient, GeminiError
from app.models.edu_ia import EduAIMessageRole
from app.repositories.edu_ia import EduAIRepository
from app.repositories.subjects import SubjectRepository
from app.repositories.tasks import TaskRepository
from app.schemas.edu_ia import (
    EduAIConversationCreate,
    EduAIConversationDetail,
    EduAIConversationOutput,
    EduAIMessageCreate,
    EduAIMessageOutput,
    EduAIStatus,
)

router = APIRouter(prefix="/api/edu-ia", tags=["edu ia"])


def get_edu_ai_client() -> GeminiClient:
    settings = get_settings()
    if not settings.edu_ai_enabled or not settings.gemini_api_key:
        raise ApiError(
            503,
            "edu_ai_unavailable",
            "O EDU IA ainda não está configurado para responder perguntas.",
        )
    return GeminiClient(settings.gemini_api_key, settings.gemini_model)


@router.get("", response_model=EduAIStatus)
def edu_ia_status(
    user: CurrentUser,
    settings: Annotated[object, Depends(get_settings)],
) -> EduAIStatus:
    del user
    return EduAIStatus(available=settings.edu_ai_enabled)


def get_owned_conversation(db: Session, conversation_id: UUID, user_id: UUID):
    conversation = EduAIRepository.get_conversation(db, conversation_id, user_id)
    if conversation is None:
        raise ApiError(404, "edu_ai_conversation_not_found", "Conversa não encontrada.")
    return conversation


def resolve_context(
    db: Session, user_id: UUID, data: EduAIConversationCreate
) -> tuple[UUID | None, UUID | None, str]:
    subject = None
    task = None
    if data.subject_id is not None:
        subject = SubjectRepository.get_for_user(db, data.subject_id, user_id)
        if subject is None:
            raise ApiError(404, "subject_not_found", "Disciplina não encontrada.")
    if data.task_id is not None:
        task = TaskRepository.get_for_user(db, data.task_id, user_id)
        if task is None:
            raise ApiError(404, "task_not_found", "Tarefa não encontrada.")
        if subject is not None and task.subject_id != subject.id:
            raise ApiError(422, "invalid_edu_ai_context", "A tarefa não pertence à disciplina.")
        subject = task.subject
    if task is not None:
        return subject.id, task.id, task.title
    if subject is not None:
        return subject.id, None, subject.name
    return None, None, "Nova conversa"


def tutor_instruction(db: Session, user_id: UUID, conversation) -> str:
    subject = (
        SubjectRepository.get_for_user(db, conversation.subject_id, user_id)
        if conversation.subject_id
        else None
    )
    task = (
        TaskRepository.get_for_user(db, conversation.task_id, user_id)
        if conversation.task_id
        else None
    )
    context = ["Você é EDU IA, um tutor acadêmico do EduTrack."]
    context.append("Responda sempre em português do Brasil, com clareza e passo a passo.")
    context.append("Ajude a aprender; não invente fontes, notas ou prazos.")
    if subject is not None:
        context.append(f"Disciplina: {subject.name}.")
        if subject.description:
            context.append(f"Descrição da disciplina: {subject.description}")
    if task is not None:
        context.append(f"Tarefa: {task.title}.")
        if task.description:
            context.append(f"Descrição da tarefa: {task.description}")
    return "\n".join(context)


def ensure_request_budget(db: Session, user_id: UUID) -> None:
    settings = get_settings()
    now = datetime.now(UTC)
    minute_count = EduAIRepository.count_student_messages_since(
        db, user_id, now - timedelta(minutes=1)
    )
    day_count = EduAIRepository.count_student_messages_since(
        db, user_id, now - timedelta(days=1)
    )
    if (
        minute_count >= settings.edu_ai_requests_per_minute
        or day_count >= settings.edu_ai_requests_per_day
    ):
        raise ApiError(
            429,
            "edu_ai_rate_limited",
            "Você atingiu o limite de perguntas do EDU IA. Tente novamente mais tarde.",
        )


@router.get("/conversations", response_model=list[EduAIConversationOutput])
def list_conversations(
    user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> list:
    return EduAIRepository.list_conversations(db, user.id)


@router.post(
    "/conversations",
    response_model=EduAIConversationOutput,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    data: EduAIConversationCreate,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> object:
    subject_id, task_id, title = resolve_context(db, user.id, data)
    return EduAIRepository.create_conversation(db, user.id, title, subject_id, task_id)


@router.get("/conversations/{conversation_id}", response_model=EduAIConversationDetail)
def get_conversation(
    conversation_id: UUID,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> object:
    return get_owned_conversation(db, conversation_id, user.id)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: UUID,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    EduAIRepository.delete_conversation(db, get_owned_conversation(db, conversation_id, user.id))


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=EduAIMessageOutput,
    status_code=status.HTTP_201_CREATED,
)
def create_message(
    conversation_id: UUID,
    data: EduAIMessageCreate,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    client: Annotated[GeminiClient, Depends(get_edu_ai_client)],
) -> object:
    conversation = get_owned_conversation(db, conversation_id, user.id)
    ensure_request_budget(db, user.id)
    EduAIRepository.add_message(db, conversation, EduAIMessageRole.USER, data.content)
    history = [
        {"role": message.role.value, "content": message.content}
        for message in EduAIRepository.list_messages(db, conversation_id)[-12:]
    ]
    try:
        reply = client.generate_reply(tutor_instruction(db, user.id, conversation), history)
    except GeminiError as exception:
        raise ApiError(
            503,
            exception.code,
            "O EDU IA não conseguiu responder agora. Sua pergunta foi salva; tente novamente.",
        ) from exception
    return EduAIRepository.add_message(db, conversation, EduAIMessageRole.ASSISTANT, reply)

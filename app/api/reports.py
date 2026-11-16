from datetime import date, datetime, timedelta
from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.api.errors import ApiError
from app.core.database import get_db
from app.models.subject import Subject
from app.models.task import AcademicTask
from app.services.reports import render_weekly_pdf

router = APIRouter(prefix="/api/reports", tags=["relatórios"])


@router.get(
    "/generate",
    response_class=Response,
    responses={
        200: {"content": {"application/pdf": {}}, "description": "Relatório semanal em PDF"},
        401: {"description": "Sessão necessária"},
    },
)
def generate_report(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    week_start: date | None = None,
    timezone: Annotated[str, Query(max_length=64)] = "America/Sao_Paulo",
) -> Response:
    """Exporta a semana (segunda a domingo) que contém week_start, sem alterar dados."""
    try:
        zone = ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise ApiError(422, "invalid_timezone", "Informe um fuso horário válido.") from error
    selected = week_start or datetime.now(zone).date()
    if not date(1900, 1, 1) <= selected <= date(9998, 12, 31):
        raise ApiError(422, "invalid_week", "Informe uma data entre 1900 e 9998.")
    first = selected - timedelta(days=selected.weekday())
    subjects = list(db.scalars(select(Subject).where(Subject.user_id == user.id)))
    tasks = list(db.scalars(select(AcademicTask).join(Subject).where(Subject.user_id == user.id)))
    content = render_weekly_pdf(user.name, subjects, tasks, first, zone)
    return Response(
        content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="edutrack-semana-{first.isoformat()}.pdf"'
            ),
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )

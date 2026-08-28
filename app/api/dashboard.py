from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.core.database import get_db
from app.schemas.dashboard import DashboardOutput
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardOutput)
def dashboard(
    user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> DashboardOutput:
    return DashboardService.build(db, user.id, date.today())

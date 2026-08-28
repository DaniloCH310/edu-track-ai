from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.errors import register_error_handlers
from app.api.subjects import router as subjects_router
from app.api.tasks import router as tasks_router


def create_app() -> FastAPI:
    application = FastAPI(title="EduTrack AI API")
    register_error_handlers(application)
    application.include_router(auth_router)
    application.include_router(subjects_router)
    application.include_router(tasks_router)
    application.include_router(dashboard_router)

    static_root = Path(__file__).parent / "static"
    application.mount("/static", StaticFiles(directory=static_root), name="static")

    @application.get("/", include_in_schema=False)
    def frontend() -> FileResponse:
        return FileResponse(static_root / "index.html")

    @application.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()

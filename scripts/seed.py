from datetime import UTC, date, datetime, timedelta
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.subject import Subject
from app.models.task import AcademicTask, TaskStatus
from app.models.user import User

SUBJECTS = (
    ("python", "Python Aplicado", "Prof. Marina", 80, "#6750A4"),
    ("ux", "UX e Interfaces", "Prof. Rafael", 60, "#00796B"),
    ("database", "Banco de Dados", "Prof. Carlos", 60, "#E67E22"),
)


def stable_id(email: str, kind: str, key: str):
    return uuid5(NAMESPACE_URL, f"edutrack:{email}:{kind}:{key}")


def seed_demo(db: Session, email: str, password: str) -> User:
    normalized_email = email.strip().lower()
    user = db.scalar(select(User).where(User.email == normalized_email))
    if user is None:
        user = User(
            id=stable_id(normalized_email, "user", "demo"),
            name="Ana Estudante",
            email=normalized_email,
            password_hash=hash_password(password),
        )
        db.add(user)
    else:
        user.name = "Ana Estudante"
        user.password_hash = hash_password(password)
        user.is_active = True
    db.flush()

    subject_by_key: dict[str, Subject] = {}
    for key, name, professor, workload, color in SUBJECTS:
        subject_id = stable_id(normalized_email, "subject", key)
        subject = db.get(Subject, subject_id)
        if subject is None:
            subject = Subject(id=subject_id, user_id=user.id)
            db.add(subject)
        subject.name = name
        subject.professor = professor
        subject.workload_hours = workload
        subject.period = "2026.2"
        subject.color = color
        subject_by_key[key] = subject
    db.flush()

    today = date.today()
    task_data = (
        ("python-list", "python", "Finalizar lista de Python", 1, TaskStatus.IN_PROGRESS),
        ("python-project", "python", "Revisar projeto final", 5, TaskStatus.PENDING),
        ("ux-flow", "ux", "Validar fluxo do protótipo", 2, TaskStatus.PENDING),
        ("database-model", "database", "Entregar modelo relacional", -1, TaskStatus.COMPLETED),
        ("database-review", "database", "Revisar normalização", 8, TaskStatus.PENDING),
    )
    for key, subject_key, title, days, task_status in task_data:
        task_id = stable_id(normalized_email, "task", key)
        task = db.get(AcademicTask, task_id)
        if task is None:
            task = AcademicTask(id=task_id, subject_id=subject_by_key[subject_key].id)
            db.add(task)
        task.subject_id = subject_by_key[subject_key].id
        task.title = title
        task.description = "Conteúdo demonstrativo do EduTrack AI."
        task.due_date = today + timedelta(days=days)
        task.status = task_status
        task.completed_at = datetime.now(UTC) if task_status == TaskStatus.COMPLETED else None

    db.commit()
    db.refresh(user)
    return user


def main() -> None:
    settings = get_settings()
    with SessionLocal() as db:
        seed_demo(db, str(settings.demo_email), settings.demo_password)
    print("Dados de demonstração preparados com sucesso.")


if __name__ == "__main__":
    main()

# EduTrack AI MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Substituir o protótipo Streamlit por um MVP web responsivo com frontend HTML/CSS/JavaScript, API FastAPI, PostgreSQL, autenticação segura e recuperação real de senha pelo Gmail.

**Architecture:** Um único serviço FastAPI entrega o frontend estático e expõe uma API REST em `/api`. Serviços de domínio coordenam autenticação e regras, repositórios SQLAlchemy isolam PostgreSQL e Alembic versiona o schema. O navegador mantém sessão por JWT em cookie `HttpOnly` e usa módulos JavaScript pequenos para cada área da interface.

**Tech Stack:** Python 3.12+, FastAPI, Uvicorn, SQLAlchemy 2, Alembic, PostgreSQL 16 portátil para Windows, psycopg 3, Pydantic Settings, PyJWT, pwdlib/Argon2, Gmail SMTP, HTML5, CSS3, JavaScript ES modules, PowerShell, pytest, HTTPX e Playwright para Python.

**Spec:** `docs/superpowers/specs/2026-08-27-edutrack-mvp-rearchitecture-design.md`

## Global Constraints

- O escopo é apenas o MVP aprovado; cronômetro, IA generativa, notificações push, métricas avançadas e relatórios PDF permanecem fora.
- O frontend deve usar HTML, CSS e JavaScript sem framework.
- O backend deve usar FastAPI e servir frontend e API no mesmo processo.
- A persistência deve usar PostgreSQL; testes de integração não podem substituir o banco por SQLite.
- Todos os dados de disciplinas e tarefas devem ser isolados pelo usuário autenticado.
- JWT deve permanecer em cookie `HttpOnly`; JavaScript não pode ler nem persistir o token.
- Credenciais PostgreSQL, JWT e Gmail devem vir de variáveis de ambiente; `.env` nunca será versionado.
- A recuperação de senha deve enviar e-mail real pelo Gmail SMTP usando senha de aplicativo.
- A interface deve preservar a identidade roxa do protótipo, suportar tema claro/escuro e funcionar sem overflow horizontal no celular.
- Novos textos visíveis ao usuário devem estar em português do Brasil.
- O protótipo `app.py` deve permanecer preservado até a validação final da nova aplicação.

## File Map

```text
.env.example                         nomes e exemplos seguros de configuração
.gitignore                           segredos, ambientes, binários e dados locais
pyproject.toml                       dependências, pytest e Ruff
alembic.ini                          configuração de migrações
alembic/env.py                       metadata e URL do banco
alembic/versions/*_initial_schema.py schema inicial
app/main.py                          criação do FastAPI, middleware, rotas e frontend
app/api/dependencies.py              sessão de banco e usuário autenticado
app/api/errors.py                    envelope de erro estável
app/api/auth.py                      endpoints de autenticação e recuperação
app/api/subjects.py                  endpoints de disciplinas
app/api/tasks.py                     endpoints de tarefas
app/api/dashboard.py                 endpoint de métricas
app/core/config.py                   Pydantic Settings
app/core/database.py                 engine, SessionLocal e Base
app/core/security.py                 hash, JWT e tokens aleatórios
app/models/user.py                   users e password_reset_tokens
app/models/subject.py                subjects
app/models/task.py                   academic_tasks e status canônico
app/repositories/users.py            consultas de usuários e tokens
app/repositories/subjects.py         consultas isoladas de disciplinas
app/repositories/tasks.py            consultas isoladas e filtradas de tarefas
app/schemas/auth.py                  entradas e saídas de autenticação
app/schemas/subject.py               entradas e saídas de disciplinas
app/schemas/task.py                  entradas, filtros e saídas de tarefas
app/schemas/dashboard.py             saída agregada do dashboard
app/services/auth.py                 cadastro, login e recuperação
app/services/email.py                Gmail SMTP
app/services/dashboard.py            cálculos de progresso e prazo
app/static/index.html                shell da aplicação
app/static/css/tokens.css             tokens de tema
app/static/css/app.css                layout e componentes
app/static/js/api.js                  cliente HTTP e tratamento de erro
app/static/js/auth.js                 login, cadastro e recuperação
app/static/js/state.js                estado mínimo do frontend
app/static/js/ui.js                   modais, toasts, tema e navegação
app/static/js/dashboard.js            renderização do dashboard
app/static/js/subjects.js             CRUD de disciplinas
app/static/js/tasks.js                CRUD, busca e filtros de tarefas
app/static/js/app.js                  inicialização e roteamento da SPA simples
scripts/seed.py                       seed idempotente de demonstração
scripts/setup-postgres.ps1            baixa e inicializa PostgreSQL portátil
scripts/start-postgres.ps1            inicia clusters dev/test sem serviço do Windows
scripts/stop-postgres.ps1             encerra clusters de forma controlada
scripts/start-app.ps1                 migra e inicia FastAPI
tests/conftest.py                     banco PostgreSQL isolado, cliente e factories
tests/api/test_health.py              smoke test da aplicação
tests/api/test_auth.py                autenticação e autorização
tests/api/test_password_reset.py      Gmail e tokens de recuperação
tests/api/test_subjects.py            CRUD e isolamento de disciplinas
tests/api/test_tasks.py               CRUD, filtros e isolamento de tarefas
tests/api/test_dashboard.py           métricas e prazos
tests/e2e/test_student_flow.py         fluxo principal no navegador
README.md                              configuração e comandos operacionais
```

---

### Task 1: Fundação FastAPI, configuração, PostgreSQL e migração inicial

**Files:**
- Create: `.gitignore`
- Create: `.env.example`
- Create: `pyproject.toml`
- Create: `scripts/setup-postgres.ps1`
- Create: `scripts/start-postgres.ps1`
- Create: `scripts/stop-postgres.ps1`
- Create: `scripts/start-app.ps1`
- Create: `alembic.ini`
- Create: `alembic/env.py`
- Create: `alembic/script.py.mako`
- Create: `alembic/versions/20260827_0001_initial_schema.py`
- Create: `app/__init__.py`
- Create: `app/main.py`
- Create: `app/api/__init__.py`
- Create: `app/api/errors.py`
- Create: `app/core/__init__.py`
- Create: `app/core/config.py`
- Create: `app/core/database.py`
- Create: `app/models/__init__.py`
- Create: `app/models/user.py`
- Create: `app/models/subject.py`
- Create: `app/models/task.py`
- Create: `tests/conftest.py`
- Create: `tests/api/test_health.py`

**Interfaces:**
- Consumes: approved design spec only.
- Produces: `Settings`, `get_settings()`, `Base`, `SessionLocal`, `get_db()`, SQLAlchemy models `User`, `PasswordResetToken`, `Subject`, `AcademicTask`, enum `TaskStatus`, and `create_app() -> FastAPI`.

- [ ] **Step 1: Initialize version control and ignore local state**

Run:

```powershell
git init
```

Create `.gitignore` with:

```gitignore
.env
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
.coverage
htmlcov/
tmp/
.superpowers/
.tools/
.data/
playwright-report/
test-results/
```

- [ ] **Step 2: Write the failing health test**

```python
# tests/api/test_health.py
def test_health_returns_ok(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 3: Run the test to verify the foundation is absent**

Run:

```powershell
py -3 -m pytest tests/api/test_health.py -v
```

Expected: FAIL because the application package and test fixtures do not exist.

- [ ] **Step 4: Define dependencies and configuration**

Create `pyproject.toml` with Python `>=3.12`, application dependencies `fastapi`, `uvicorn[standard]`, `sqlalchemy>=2`, `alembic`, `psycopg[binary]`, `pydantic-settings`, `pyjwt`, `pwdlib[argon2]`, `email-validator`, `python-multipart` and `slowapi`; development dependencies are `pytest`, `pytest-cov`, `httpx`, `playwright` and `ruff`.

Implement:

```python
# app/core/config.py
from functools import lru_cache
from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "EduTrack AI"
    environment: str = "development"
    database_url: str
    jwt_secret: str
    jwt_expire_minutes: int = 60
    password_reset_minutes: int = 30
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: EmailStr
    smtp_password: str
    smtp_from_email: EmailStr
    frontend_url: str = "http://localhost:8000"
    cookie_secure: bool = False

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

`.env.example` must declare matching variables using non-secret examples.

- [ ] **Step 5: Implement database primitives and models**

Use UUID primary keys, timezone-aware timestamps and the exact fields from the approved spec. Define:

```python
class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
```

Set `Subject.tasks` to `cascade="all, delete-orphan"` and `AcademicTask.subject_id` to `ondelete="CASCADE"`. Add indexes on `users.email`, `subjects.user_id`, `academic_tasks.subject_id`, `academic_tasks.status` and `academic_tasks.due_date`.

- [ ] **Step 6: Add the initial Alembic migration and portable PostgreSQL scripts**

`scripts/setup-postgres.ps1` must download the official Windows x86-64 binary archive linked by PostgreSQL.org (`https://sbp.enterprisedb.com/getfile.jsp?fileid=1260422`, PostgreSQL 16.15), verify HTTP success, non-zero length and ZIP extraction, then locate `bin\initdb.exe`. Extract to `.tools/postgresql`; initialize `.data/postgresql/dev` and `.data/postgresql/test` only when `PG_VERSION` is absent. Use ports `54329` and `54330`, UTF-8, locale `Portuguese_Brazil.1252` when available with fallback to `C`, and SCRAM authentication. Create databases `edutrack` and `edutrack_test` idempotently.

`scripts/start-postgres.ps1` accepts `-Cluster Dev|Test|All`, uses `pg_ctl status` before `pg_ctl start`, waits with `pg_isready` and writes logs under `.data/postgresql/logs`. `scripts/stop-postgres.ps1` accepts the same parameter and uses `pg_ctl stop -m fast` only for running clusters. `scripts/start-app.ps1` starts `Dev`, verifies `.env`, runs `.venv\Scripts\python.exe -m alembic upgrade head` and then Uvicorn on `127.0.0.1:8000`.

`.env.example` uses `postgresql+psycopg://edutrack:edutrack_local@127.0.0.1:54329/edutrack`; test fixtures use `postgresql+psycopg://edutrack:edutrack_test@127.0.0.1:54330/edutrack_test`.

- [ ] **Step 7: Implement the app factory and stable error envelope**

```python
# app/main.py
from fastapi import FastAPI

def create_app() -> FastAPI:
    app = FastAPI(title="EduTrack AI API")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app

app = create_app()
```

Register handlers in `app/api/errors.py` so validation errors use `{"error": {"code", "message", "fields"}}` and unexpected errors use a safe message without exception details.

- [ ] **Step 8: Build the environment and verify migrations and health**

Run:

```powershell
Copy-Item .env.example .env
py -3 -m pip install -e ".[dev]"
.\scripts\setup-postgres.ps1
.\.venv\Scripts\python.exe -m alembic upgrade head
py -3 -m pytest tests/api/test_health.py -v
```

Expected: migration completes and the health test passes.

- [ ] **Step 9: Commit the foundation**

```powershell
git add .gitignore .env.example pyproject.toml scripts alembic.ini alembic app tests
git commit -m "chore: scaffold FastAPI and PostgreSQL foundation"
```

---

### Task 2: Security primitives and authenticated-user dependency

**Files:**
- Create: `app/core/security.py`
- Create: `app/api/dependencies.py`
- Create: `app/repositories/users.py`
- Create: `app/schemas/auth.py`
- Create: `tests/unit/test_security.py`
- Create: `tests/api/test_auth.py`

**Interfaces:**
- Consumes: `Settings`, `SessionLocal`, `User`.
- Produces: `hash_password(password: str) -> str`, `verify_password(password: str, password_hash: str) -> bool`, `create_access_token(user_id: UUID) -> str`, `decode_access_token(token: str) -> UUID`, `get_current_user() -> User`, `UserRepository.get_by_email()` and auth Pydantic schemas.

- [ ] **Step 1: Write failing password and JWT tests**

```python
def test_password_hash_never_contains_plaintext():
    encoded = hash_password("Senha-Forte-123")
    assert "Senha-Forte-123" not in encoded
    assert verify_password("Senha-Forte-123", encoded)
    assert not verify_password("senha-incorreta", encoded)

def test_access_token_round_trip(user_id):
    token = create_access_token(user_id)
    assert decode_access_token(token) == user_id
```

- [ ] **Step 2: Run the focused tests and confirm failure**

Run:

```powershell
py -3 -m pytest tests/unit/test_security.py -v
```

Expected: FAIL because `app.core.security` does not exist.

- [ ] **Step 3: Implement Argon2 password hashing and JWT**

Use `pwdlib.PasswordHash.recommended()` and PyJWT with `sub`, `iat`, `exp` and `type="access"`. Reject missing subject, wrong type, invalid signature and expired tokens with one `InvalidTokenError` mapped to HTTP 401 by the dependency.

- [ ] **Step 4: Write failing authenticated dependency tests**

```python
def test_protected_route_rejects_missing_cookie(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "not_authenticated"

def test_protected_route_rejects_deleted_user(client, access_cookie_for_deleted_user):
    response = client.get("/api/auth/me", cookies=access_cookie_for_deleted_user)
    assert response.status_code == 401
```

- [ ] **Step 5: Implement repository, schemas and dependency**

Define `RegisterInput(name, email, password)`, `LoginInput(email, password)`, `UserOutput(id, name, email)` and password validators requiring at least 10 characters, uppercase, lowercase and digit. `get_current_user` must read cookie `edutrack_session`, decode the JWT, load an active user and return the same neutral 401 response for all invalid session states.

- [ ] **Step 6: Run security and dependency tests**

Run:

```powershell
py -3 -m pytest tests/unit/test_security.py tests/api/test_auth.py -v
```

Expected: all implemented tests pass.

- [ ] **Step 7: Commit security primitives**

```powershell
git add app/core/security.py app/api/dependencies.py app/repositories/users.py app/schemas/auth.py tests/unit/test_security.py tests/api/test_auth.py
git commit -m "feat: add password and session security"
```

---

### Task 3: Registration, login, logout and current-user API

**Files:**
- Create: `app/services/auth.py`
- Create: `app/api/auth.py`
- Modify: `app/main.py`
- Modify: `tests/api/test_auth.py`

**Interfaces:**
- Consumes: Task 2 security functions, `UserRepository`, auth schemas and `get_current_user`.
- Produces: `AuthService.register()`, `AuthService.authenticate()`, and routes `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`.

- [ ] **Step 1: Add failing registration and session tests**

```python
def test_register_sets_http_only_cookie(client):
    response = client.post("/api/auth/register", json={
        "name": "Ana Estudante",
        "email": "ana@example.com",
        "password": "Senha-Forte-123",
    })
    assert response.status_code == 201
    assert response.json()["email"] == "ana@example.com"
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "SameSite=lax" in response.headers["set-cookie"]

def test_login_and_logout_control_session(client, user_factory):
    user_factory(email="ana@example.com", password="Senha-Forte-123")
    assert client.post("/api/auth/login", json={
        "email": "ana@example.com", "password": "Senha-Forte-123"
    }).status_code == 200
    assert client.get("/api/auth/me").status_code == 200
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401
```

- [ ] **Step 2: Run the auth API tests and confirm failure**

Run:

```powershell
py -3 -m pytest tests/api/test_auth.py -v
```

Expected: new cases fail with missing routes.

- [ ] **Step 3: Implement service and endpoints**

Normalize e-mail with `strip().lower()`. Registration must return 409 with code `email_unavailable` for duplicates. Login must return the same 401 `invalid_credentials` for unknown email and wrong password. Both successful registration and login set `edutrack_session`; logout deletes it using the same path and SameSite settings.

- [ ] **Step 4: Add and pass isolation-facing auth cases**

Cover inactive users, duplicate e-mail with different casing, malformed payloads and cookies with invalid JWT. Run:

```powershell
py -3 -m pytest tests/api/test_auth.py -v
```

Expected: all auth tests pass.

- [ ] **Step 5: Commit authentication endpoints**

```powershell
git add app/services/auth.py app/api/auth.py app/main.py tests/api/test_auth.py
git commit -m "feat: implement user authentication API"
```

---

### Task 4: Gmail password recovery with one-use expiring tokens

**Files:**
- Create: `app/services/email.py`
- Modify: `app/core/security.py`
- Modify: `app/repositories/users.py`
- Modify: `app/services/auth.py`
- Modify: `app/schemas/auth.py`
- Modify: `app/api/auth.py`
- Create: `tests/api/test_password_reset.py`

**Interfaces:**
- Consumes: `PasswordResetToken`, `Settings`, `UserRepository` and password hashing.
- Produces: `generate_reset_token() -> tuple[str, str]`, `EmailService.send_password_reset(to_email: str, reset_url: str) -> None`, `AuthService.request_password_reset(email: str) -> None`, `AuthService.reset_password(token: str, new_password: str) -> None`.

- [ ] **Step 1: Write failing token-lifecycle tests**

```python
def test_forgot_password_is_neutral_and_sends_for_known_email(client, user_factory, email_spy):
    user_factory(email="ana@example.com")
    known = client.post("/api/auth/forgot-password", json={"email": "ana@example.com"})
    unknown = client.post("/api/auth/forgot-password", json={"email": "ninguem@example.com"})
    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()
    assert email_spy.call_count == 1

def test_reset_token_is_single_use(client, reset_token_factory):
    raw_token = reset_token_factory(email="ana@example.com")
    payload = {"token": raw_token, "new_password": "Nova-Senha-456"}
    assert client.post("/api/auth/reset-password", json=payload).status_code == 204
    assert client.post("/api/auth/reset-password", json=payload).status_code == 400
```

- [ ] **Step 2: Run recovery tests and verify failure**

Run:

```powershell
py -3 -m pytest tests/api/test_password_reset.py -v
```

Expected: FAIL because recovery routes and e-mail service do not exist.

- [ ] **Step 3: Implement random tokens and repository methods**

Generate 32 random bytes with `secrets.token_urlsafe(32)`, persist `sha256(raw_token).hexdigest()`, set `expires_at` from `password_reset_minutes`, invalidate previous unused tokens for the same user and atomically mark the accepted token as used.

- [ ] **Step 4: Implement Gmail SMTP adapter**

Use `smtplib.SMTP(settings.smtp_host, settings.smtp_port)`, `starttls(context=ssl.create_default_context())`, `login()` and `EmailMessage`. Subject: `Redefina sua senha no EduTrack AI`. The body must include `${frontend_url}/?reset_token=<urlencoded-token>` and the configured expiration in minutes. Do not log the raw token or SMTP password.

- [ ] **Step 5: Implement neutral request and reset routes**

`POST /api/auth/forgot-password` returns 202 and `{"message": "Se o e-mail estiver cadastrado, enviaremos as instruções."}` for known and unknown addresses. `POST /api/auth/reset-password` returns 204 on success and 400 `invalid_or_expired_token` for unknown, used or expired tokens. Configure SlowAPI by client address in `create_app()`: `POST /api/auth/login` and `POST /api/auth/forgot-password` accept at most five attempts per minute, with a stable 429 envelope using code `rate_limited`. Keep the limiter storage in memory for this single-process MVP.

- [ ] **Step 6: Verify recovery edge cases**

Add tests for expired token, malformed token, invalid new password, previous token invalidation, SMTP failure returning safe 503 `email_unavailable`, successful login only with the new password, and the sixth login/recovery attempt from one client returning 429 while a different client address remains unaffected. Run:

```powershell
py -3 -m pytest tests/api/test_password_reset.py tests/api/test_auth.py -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit password recovery**

```powershell
git add app tests/api/test_password_reset.py tests/api/test_auth.py
git commit -m "feat: add Gmail password recovery"
```

---

### Task 5: Subjects CRUD with ownership enforcement

**Files:**
- Create: `app/schemas/subject.py`
- Create: `app/repositories/subjects.py`
- Create: `app/api/subjects.py`
- Modify: `app/main.py`
- Create: `tests/api/test_subjects.py`

**Interfaces:**
- Consumes: `Subject`, `get_db()`, `get_current_user()`.
- Produces: `SubjectCreate`, `SubjectUpdate`, `SubjectOutput`, `SubjectRepository.list_for_user()`, `get_for_user()`, `create()`, `update()`, `delete()`, and all `/api/subjects` routes.

- [ ] **Step 1: Write failing CRUD and ownership tests**

```python
def test_subject_crud(client, authenticated_user):
    created = client.post("/api/subjects", json={
        "name": "Python Aplicado",
        "professor": "Marina Costa",
        "workload_hours": 80,
        "description": "Lógica, dados e automação.",
        "period": "2026.2",
        "color": "#6750A4",
        "start_date": "2026-08-01",
        "end_date": "2026-12-15",
    })
    assert created.status_code == 201
    subject_id = created.json()["id"]
    assert client.get("/api/subjects").json()[0]["id"] == subject_id
    assert client.put(f"/api/subjects/{subject_id}", json={
        **created.json(), "name": "Python e Dados"
    }).json()["name"] == "Python e Dados"
    assert client.delete(f"/api/subjects/{subject_id}").status_code == 204

def test_user_cannot_access_another_users_subject(client, other_user_subject):
    response = client.get(f"/api/subjects/{other_user_subject.id}")
    assert response.status_code == 404
```

- [ ] **Step 2: Run subject tests and confirm failure**

Run:

```powershell
py -3 -m pytest tests/api/test_subjects.py -v
```

Expected: FAIL with missing subject routes.

- [ ] **Step 3: Implement subject schemas and repository**

Validate trimmed name, positive workload, `#RRGGBB`, and `end_date >= start_date`. Every select, update and delete must include both subject id and `user_id`. Return 404 rather than 403 when another user owns the id.

- [ ] **Step 4: Implement subject routes and cascade behavior**

Return 201 on create, ordered list by lowercase name, 200 on get/update and 204 on delete. Deleting a subject must remove its tasks at database level.

- [ ] **Step 5: Verify validation, cascade and isolation**

Add tests for blank name, zero workload, invalid color, reversed dates, another user's update/delete and cascade removal. Run:

```powershell
py -3 -m pytest tests/api/test_subjects.py -v
```

Expected: all subject tests pass.

- [ ] **Step 6: Commit subjects**

```powershell
git add app/schemas/subject.py app/repositories/subjects.py app/api/subjects.py app/main.py tests/api/test_subjects.py
git commit -m "feat: add isolated subjects CRUD"
```

---

### Task 6: Academic tasks CRUD, filters and status transitions

**Files:**
- Create: `app/schemas/task.py`
- Create: `app/repositories/tasks.py`
- Create: `app/api/tasks.py`
- Modify: `app/main.py`
- Create: `tests/api/test_tasks.py`

**Interfaces:**
- Consumes: `AcademicTask`, `TaskStatus`, `SubjectRepository.get_for_user()` and authenticated user.
- Produces: `TaskCreate`, `TaskUpdate`, `TaskStatusUpdate`, `TaskOutput`, `TaskRepository.list_for_user(...)`, and all `/api/tasks` routes.

- [ ] **Step 1: Write failing task workflow tests**

```python
def test_task_crud_and_completion_timestamp(client, owned_subject):
    created = client.post("/api/tasks", json={
        "subject_id": str(owned_subject.id),
        "title": "Finalizar exercício",
        "description": "Resolver a lista 3.",
        "due_date": "2026-09-01",
        "status": "pending",
    })
    assert created.status_code == 201
    task_id = created.json()["id"]
    completed = client.patch(f"/api/tasks/{task_id}/status", json={"status": "completed"})
    assert completed.status_code == 200
    assert completed.json()["completed_at"] is not None

def test_task_cannot_reference_another_users_subject(client, other_user_subject):
    response = client.post("/api/tasks", json={
        "subject_id": str(other_user_subject.id),
        "title": "Invasão",
        "due_date": "2026-09-01",
        "status": "pending",
    })
    assert response.status_code == 404
```

- [ ] **Step 2: Run task tests and confirm failure**

Run:

```powershell
py -3 -m pytest tests/api/test_tasks.py -v
```

Expected: FAIL with missing routes.

- [ ] **Step 3: Implement schemas and ownership-aware repository**

`list_for_user` signature:

```python
def list_for_user(
    db: Session,
    user_id: UUID,
    *,
    query: str | None = None,
    status: TaskStatus | None = None,
    subject_id: UUID | None = None,
    order: Literal["due_asc", "due_desc", "created_desc"] = "due_asc",
) -> list[AcademicTask]: ...
```

Search must use case-insensitive matching over title and description. All task access must join `subjects` and filter `Subject.user_id == user_id`.

- [ ] **Step 4: Implement routes and completion semantics**

Creating or moving a task to `completed` sets `completed_at` to the current UTC timestamp. Moving it away from completed clears `completed_at`. Return 404 for inaccessible task or subject ids.

- [ ] **Step 5: Verify filters, ordering and tenant isolation**

Add tests covering search, each status, subject filter, all order modes, invalid enum, cross-user list leakage, update, delete and completion reversal. Run:

```powershell
py -3 -m pytest tests/api/test_tasks.py -v
```

Expected: all task tests pass.

- [ ] **Step 6: Commit tasks**

```powershell
git add app/schemas/task.py app/repositories/tasks.py app/api/tasks.py app/main.py tests/api/test_tasks.py
git commit -m "feat: add academic task management"
```

---

### Task 7: Dashboard calculations and API

**Files:**
- Create: `app/schemas/dashboard.py`
- Create: `app/services/dashboard.py`
- Create: `app/api/dashboard.py`
- Modify: `app/main.py`
- Create: `tests/api/test_dashboard.py`

**Interfaces:**
- Consumes: authenticated user, `Subject`, `AcademicTask`, `TaskStatus`.
- Produces: `DashboardService.build(db: Session, user_id: UUID, today: date) -> DashboardOutput` and `GET /api/dashboard`.

- [ ] **Step 1: Write failing deterministic dashboard test**

```python
def test_dashboard_metrics_are_user_scoped(client, academic_scenario):
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["total_tasks"] == 5
    assert data["completed_tasks"] == 2
    assert data["overall_progress"] == 40
    assert data["due_soon"] == 2
    assert data["overdue"] == 1
    assert [item["subject_name"] for item in data["progress_by_subject"]] == [
        "Banco de Dados", "Python Aplicado", "UX e Interfaces"
    ]
```

- [ ] **Step 2: Run dashboard test and confirm failure**

Run:

```powershell
py -3 -m pytest tests/api/test_dashboard.py -v
```

Expected: FAIL with missing dashboard route.

- [ ] **Step 3: Implement schemas and deterministic calculations**

Overall progress is `round(completed / total * 100)` or zero with no tasks. Subject progress uses the same rule per subject. `due_soon` counts non-completed tasks with `today <= due_date <= today + 3 days`; `overdue` counts non-completed tasks with `due_date < today`. Upcoming items are the first four non-completed tasks ordered by due date.

- [ ] **Step 4: Implement the endpoint with injectable date**

The service accepts `today` as an argument for deterministic tests; the route passes `date.today()`. Do not use client-provided dates for production calculations.

- [ ] **Step 5: Verify empty, completed and cross-user scenarios**

Run:

```powershell
py -3 -m pytest tests/api/test_dashboard.py tests/api/test_subjects.py tests/api/test_tasks.py -v
```

Expected: all dashboard and resource tests pass.

- [ ] **Step 6: Commit dashboard**

```powershell
git add app/schemas/dashboard.py app/services/dashboard.py app/api/dashboard.py app/main.py tests/api/test_dashboard.py
git commit -m "feat: add student progress dashboard API"
```

---

### Task 8: Frontend shell, theme, authentication and recovery flows

**Files:**
- Create: `app/static/index.html`
- Create: `app/static/css/tokens.css`
- Create: `app/static/css/app.css`
- Create: `app/static/js/api.js`
- Create: `app/static/js/auth.js`
- Create: `app/static/js/state.js`
- Create: `app/static/js/ui.js`
- Create: `app/static/js/app.js`
- Modify: `app/main.py`
- Create: `tests/e2e/test_auth_flow.py`

**Interfaces:**
- Consumes: authentication endpoints and stable API error envelope.
- Produces: `api.request(path, options)`, `auth.loadCurrentUser()`, `auth.login()`, `auth.register()`, `auth.logout()`, `auth.requestReset()`, `auth.resetPassword()`, UI modal/toast/theme helpers and frontend route states.

- [ ] **Step 1: Write failing browser authentication test**

```python
def test_user_can_register_logout_and_login(page, live_server):
    page.goto(live_server.url)
    page.get_by_role("button", name="Criar conta").click()
    page.get_by_label("Nome").fill("Ana Estudante")
    page.get_by_label("E-mail").fill("ana@example.com")
    page.get_by_label("Senha").fill("Senha-Forte-123")
    page.get_by_role("button", name="Cadastrar").click()
    page.get_by_role("heading", name="Olá, Ana Estudante").wait_for()
    page.get_by_role("button", name="Sair").click()
    page.get_by_label("E-mail").fill("ana@example.com")
    page.get_by_label("Senha").fill("Senha-Forte-123")
    page.get_by_role("button", name="Entrar").click()
    page.get_by_role("heading", name="Olá, Ana Estudante").wait_for()
```

- [ ] **Step 2: Run the browser test and confirm failure**

Run:

```powershell
py -3 -m playwright install chromium
py -3 -m pytest tests/e2e/test_auth_flow.py -v
```

Expected: FAIL because FastAPI does not yet serve the frontend.

- [ ] **Step 3: Build semantic authentication and application shells**

`index.html` must contain one visible `h1`, labeled inputs, live region for status messages, sidebar navigation and main regions for auth, dashboard, subjects and tasks. Serve static assets under `/static`; return `index.html` from `/` and the reset-token URL state.

- [ ] **Step 4: Implement shared tokens and responsive layout**

Define CSS custom properties for background, surface, text, muted text, border, primary `#6750A4`, success `#00796B`, warning `#E67E22`, danger, focus ring, radii and spacing. Use `[data-theme="dark"]` overrides. Desktop sidebar collapses below 760px; no primary content may exceed viewport width.

- [ ] **Step 5: Implement API client and auth state**

All fetches use `credentials: "same-origin"`. `api.request` parses the stable error envelope, throws an `ApiError(code, message, fields)`, redirects to auth on 401 and never reads a JWT. Persist only theme preference in `localStorage`.

- [ ] **Step 6: Implement login, registration and recovery UI**

Prevent double submission, associate server field errors to inputs, show the neutral forgot-password message, detect `reset_token` with `URLSearchParams`, submit the new password and remove the token from browser history after success.

- [ ] **Step 7: Verify auth, recovery and mobile shell**

Add Playwright cases for invalid login, registration validation, neutral recovery response, reset token success, keyboard tab order, theme persistence and 390x844 viewport without horizontal overflow. Run:

```powershell
py -3 -m pytest tests/e2e/test_auth_flow.py -v
```

Expected: all frontend authentication tests pass.

- [ ] **Step 8: Commit frontend foundation**

```powershell
git add app/static app/main.py tests/e2e/test_auth_flow.py
git commit -m "feat: build responsive authentication frontend"
```

---

### Task 9: Dashboard, subjects and tasks frontend workflows

**Files:**
- Create: `app/static/js/dashboard.js`
- Create: `app/static/js/subjects.js`
- Create: `app/static/js/tasks.js`
- Modify: `app/static/index.html`
- Modify: `app/static/css/app.css`
- Modify: `app/static/js/app.js`
- Create: `tests/e2e/test_student_flow.py`

**Interfaces:**
- Consumes: `api.request`, shared UI helpers, `/api/dashboard`, `/api/subjects` and `/api/tasks`.
- Produces: `renderDashboard()`, `renderSubjects()`, `openSubjectForm(subject?)`, `renderTasks(filters)`, `openTaskForm(task?)` and complete student MVP workflow.

- [ ] **Step 1: Write the failing primary workflow test**

```python
def test_student_manages_subject_task_and_progress(page, logged_in_page):
    page.get_by_role("link", name="Disciplinas").click()
    page.get_by_role("button", name="Nova disciplina").click()
    page.get_by_label("Nome da disciplina").fill("Python Aplicado")
    page.get_by_label("Carga horária").fill("80")
    page.get_by_role("button", name="Salvar disciplina").click()
    page.get_by_text("Python Aplicado", exact=True).wait_for()

    page.get_by_role("link", name="Tarefas").click()
    page.get_by_role("button", name="Nova tarefa").click()
    page.get_by_label("Título").fill("Finalizar exercício")
    page.get_by_label("Disciplina").select_option(label="Python Aplicado")
    page.get_by_label("Prazo").fill("2026-09-01")
    page.get_by_role("button", name="Salvar tarefa").click()
    page.get_by_label("Status de Finalizar exercício").select_option("completed")

    page.get_by_role("link", name="Dashboard").click()
    page.get_by_text("100%", exact=True).wait_for()
```

- [ ] **Step 2: Run the workflow and confirm failure**

Run:

```powershell
py -3 -m pytest tests/e2e/test_student_flow.py -v
```

Expected: FAIL because application views are not implemented.

- [ ] **Step 3: Implement dashboard rendering**

Render four metric blocks, a CSS/SVG-free progress bar list per subject, four upcoming tasks and discipline summary rows. Use semantic text for all values; the progress graphic cannot be the only representation of the percentage.

- [ ] **Step 4: Implement subjects workflow**

List subject name, professor, workload, period and progress. Use one accessible modal for create/edit, map API field errors to inputs, focus the first invalid field and require a second explicit confirmation before delete. Refresh subjects, task-filter options and dashboard after mutation.

- [ ] **Step 5: Implement tasks workflow**

Provide search input, status and subject selects and due-order select. Debounce text search by 250 ms, cancel stale fetches with `AbortController`, render Portuguese labels for canonical statuses and update status immediately with rollback plus error toast if the API fails.

- [ ] **Step 6: Add empty, loading, error and mobile states**

Each region must have skeleton/loading text, actionable empty state and retry button. At 390px, controls stack, cards remain readable and modals fit the viewport. Destructive actions use danger styling; focus returns to the triggering control when modal closes.

- [ ] **Step 7: Verify all user-visible workflows**

Extend Playwright coverage with edit/delete discipline, cascade confirmation, task edit/delete, search, each filter, API error recovery, keyboard modal close and mobile overflow. Run:

```powershell
py -3 -m pytest tests/e2e/test_student_flow.py tests/e2e/test_auth_flow.py -v
```

Expected: all E2E tests pass.

- [ ] **Step 8: Commit application frontend**

```powershell
git add app/static tests/e2e
git commit -m "feat: implement student dashboard workflows"
```

---

### Task 10: Idempotent demo seed, portable operation documentation and complete verification

**Files:**
- Create: `scripts/seed.py`
- Modify: `.env.example`
- Modify: `scripts/setup-postgres.ps1`
- Modify: `scripts/start-postgres.ps1`
- Modify: `scripts/stop-postgres.ps1`
- Modify: `scripts/start-app.ps1`
- Modify: `README.md`
- Modify: `requirements.txt`
- Modify: `Comando para iniciar servidor.txt`
- Test: `tests/integration/test_seed.py`

**Interfaces:**
- Consumes: `SessionLocal`, domain models and password hashing.
- Produces: `seed_demo(db: Session, email: str, password: str) -> User`, documented startup, migration, seed, test and Gmail setup commands.

- [ ] **Step 1: Write the failing idempotent seed test**

```python
def test_demo_seed_is_idempotent(db_session):
    first = seed_demo(db_session, "demo@example.com", "Demo-Segura-123")
    second = seed_demo(db_session, "demo@example.com", "Demo-Segura-123")
    assert first.id == second.id
    assert db_session.query(User).filter_by(email="demo@example.com").count() == 1
    assert db_session.query(Subject).filter_by(user_id=first.id).count() == 3
    assert db_session.query(AcademicTask).join(Subject).filter(Subject.user_id == first.id).count() == 5
```

- [ ] **Step 2: Run the seed test and confirm failure**

Run:

```powershell
py -3 -m pytest tests/integration/test_seed.py -v
```

Expected: FAIL because `scripts.seed` does not exist.

- [ ] **Step 3: Implement the seed command**

Create/update the configured demo user and upsert the three canonical subjects `Python Aplicado`, `UX e Interfaces` and `Banco de Dados`. Upsert five tasks by stable seed keys or deterministic UUIDs. Hash the configured password and never print it.

- [ ] **Step 4: Replace obsolete Streamlit operation files**

Update `requirements.txt` to point readers to the authoritative installation command or mirror production dependencies without Streamlit/Pandas. Replace `Comando para iniciar servidor.txt` with:

```text
Copy-Item .env.example .env
.\scripts\setup-postgres.ps1
.\scripts\start-app.ps1
Abra http://localhost:8000
Para encerrar o banco: .\scripts\stop-postgres.ps1 -Cluster All
```

Keep `app.py` during this task and label it as legacy in the README; do not execute it as the primary application.

- [ ] **Step 5: Document Gmail and local operation**

README must explain creating a Google App Password with 2-Step Verification, setting `SMTP_USERNAME`, `SMTP_PASSWORD` and `SMTP_FROM_EMAIL`, copying `.env.example`, running the portable PostgreSQL setup, starting/stopping each cluster, running `.\.venv\Scripts\python.exe -m scripts.seed`, applying migrations, running tests and opening `http://localhost:8000`. Cite the PostgreSQL Windows download page as the source of the archive and document that `.tools` and `.data` are local, ignored and removable only when the user intentionally wants to discard the database.

- [ ] **Step 6: Run complete static and automated verification**

Run:

```powershell
py -3 -m ruff check app scripts tests
py -3 -m pytest --cov=app --cov-report=term-missing
.\scripts\stop-postgres.ps1 -Cluster Test
.\scripts\start-postgres.ps1 -Cluster Test
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m scripts.seed
.\.venv\Scripts\python.exe -m scripts.seed
```

Expected: Ruff exits 0, all tests pass, coverage has no untested security-critical branch, portable PostgreSQL starts without administrative access, migration succeeds and seed succeeds twice without duplicates.

- [ ] **Step 7: Verify the visible app in desktop and mobile browsers**

Start:

```powershell
.\scripts\start-app.ps1
```

Use Playwright/browser inspection at 1440x900 and 390x844. Verify registration, login, Gmail recovery using a controlled inbox, discipline CRUD, task CRUD/status/filter, dashboard refresh, dark theme, keyboard operation and zero horizontal overflow. Capture screenshots for auth, dashboard, subjects and tasks in both viewports and compare the palette, hierarchy, spacing and copy to the approved design spec.

- [ ] **Step 8: Review repository state and commit delivery**

Run:

```powershell
git status --short
git diff --check
git log --oneline --decorate -10
```

Confirm `.env`, `.venv`, temporary PDF renders and `.superpowers` are untracked/ignored. Then commit:

```powershell
git add .env.example .gitignore pyproject.toml requirements.txt README.md "Comando para iniciar servidor.txt" scripts tests app alembic alembic.ini docs
git commit -m "docs: finalize EduTrack MVP operation and verification"
```

## Completion Gate

Before reporting completion, independently confirm:

- Every approved spec section maps to a passing test or a manually verified UI behavior.
- Portable PostgreSQL initializes without admin rights and Alembic reaches `head`.
- No route leaks another user's data.
- The Gmail recovery token expires, is single-use and is never stored in plaintext.
- The frontend never stores or reads the JWT.
- Desktop and mobile screenshots have no clipped content, accidental wrapping or horizontal overflow.
- `.env` and generated local artifacts are absent from `git status`.
- The original Streamlit prototype was preserved until the replacement passed all checks.

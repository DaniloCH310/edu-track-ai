# Google Classroom Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Conectar uma conta Google Classroom ao EduTrack e sincronizar turmas, atividades com prazo e estados de entrega sem escrever no Classroom.

**Architecture:** O FastAPI executa OAuth Authorization Code com PKCE, guarda somente o refresh token cifrado e acessa a API REST do Classroom por um gateway injetável. Um serviço transacional faz upsert por IDs externos em tabelas do schema `private`; o frontend consome apenas a API interna do EduTrack.

**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL/Supabase, httpx, cryptography/Fernet, PyJWT, HTML, CSS, JavaScript e Playwright.

**Spec:** `docs/superpowers/specs/2026-09-03-google-classroom-integration-design.md`

## Global Constraints

- A integração é somente de leitura em relação ao Google Classroom.
- Solicitar apenas `classroom.courses.readonly` e `classroom.coursework.me.readonly`.
- Nunca enviar refresh token, access token, client secret, chave Fernet ou código OAuth ao frontend, URL ou logs.
- Persistir somente o refresh token cifrado; access tokens existem apenas em memória.
- Manter funcionamento local quando `GOOGLE_CLASSROOM_ENABLED=false`.
- Não importar atividades sem prazo e informar a quantidade ignorada.
- Não excluir disciplinas ou tarefas locais durante sincronização ou desconexão.
- Usar IDs externos para que sincronismos repetidos sejam idempotentes.
- Não executar commits ou push sem autorização explícita do usuário; em cada checkpoint, revisar apenas o diff correspondente.

---

## File Structure

### Novos arquivos

- `app/integrations/__init__.py` — pacote de integrações externas.
- `app/integrations/google_classroom/__init__.py` — exports do módulo Classroom.
- `app/integrations/google_classroom/crypto.py` — cifragem Fernet do refresh token.
- `app/integrations/google_classroom/oauth.py` — geração e validação de state/PKCE.
- `app/integrations/google_classroom/client.py` — HTTP OAuth e API REST paginada.
- `app/integrations/google_classroom/sync.py` — sincronização transacional idempotente.
- `app/models/classroom.py` — conexão e vínculos externos.
- `app/repositories/classroom.py` — consultas/upserts sem commit interno.
- `app/schemas/classroom.py` — contratos da API interna.
- `app/api/classroom.py` — endpoints da integração.
- `alembic/versions/20260903_0002_google_classroom.py` — schema privado e índices.
- `app/static/js/integrations.js` — estado e ações da tela.
- `app/static/css/integrations.css` — layout responsivo da integração.
- `tests/unit/test_classroom_crypto.py` — cifragem e estado OAuth.
- `tests/unit/test_classroom_sync.py` — regras de mapeamento e idempotência.
- `tests/api/test_classroom_integration.py` — contratos HTTP e segurança.

### Arquivos modificados

- `pyproject.toml` — mover `httpx` para runtime e adicionar `cryptography`.
- `.env.example` — configuração Google desabilitada por padrão.
- `app/core/config.py` — validar credenciais, chave e HTTPS.
- `app/models/__init__.py`, `app/models/user.py`, `app/models/subject.py`, `app/models/task.py` — registrar relações e propriedades de origem.
- `app/repositories/subjects.py`, `app/repositories/tasks.py` — carregar vínculos sem N+1.
- `app/schemas/subject.py`, `app/schemas/task.py` — expor `source` e `external_url` seguros.
- `app/main.py`, `alembic/env.py` — registrar router e metadata.
- `tests/conftest.py`, `tests/unit/test_model_metadata.py` — fixtures e contrato de schema.
- `app/static/index.html`, `app/static/js/app.js`, `app/static/js/subjects.js`, `app/static/js/tasks.js` — rota, tela e selos.
- `tests/api/test_frontend.py`, `tests/e2e/test_auth_flow.py` — assets e jornada visual.
- `README.md` — configuração Google Cloud e operação da sincronização.

---

### Task 1: Configuração, cifragem e estado OAuth

**Files:**
- Modify: `pyproject.toml`
- Modify: `.env.example`
- Modify: `app/core/config.py`
- Create: `app/integrations/__init__.py`
- Create: `app/integrations/google_classroom/__init__.py`
- Create: `app/integrations/google_classroom/crypto.py`
- Create: `app/integrations/google_classroom/oauth.py`
- Create: `tests/unit/test_classroom_crypto.py`
- Modify: `tests/conftest.py`

**Interfaces:**
- Produces: `encrypt_refresh_token(token: str, key: str) -> str`.
- Produces: `decrypt_refresh_token(ciphertext: str, key: str) -> str`.
- Produces: `OAuthContext(state: str, verifier: str, challenge: str, cookie: str)`.
- Produces: `create_oauth_context(user_id: UUID, secret: str, now: datetime | None = None) -> OAuthContext`.
- Produces: `validate_oauth_context(cookie: str, returned_state: str, user_id: UUID, secret: str, now: datetime | None = None) -> str`, retornando o verifier.

- [x] **Step 1: Escrever os testes de configuração e cifragem**

```python
from cryptography.fernet import Fernet, InvalidToken
from pydantic import ValidationError

from app.core.config import Settings
from app.integrations.google_classroom.crypto import (
    decrypt_refresh_token,
    encrypt_refresh_token,
)


def test_refresh_token_round_trip_never_returns_plaintext():
    key = Fernet.generate_key().decode()
    encrypted = encrypt_refresh_token("refresh-secret", key)
    assert encrypted != "refresh-secret"
    assert decrypt_refresh_token(encrypted, key) == "refresh-secret"


def test_invalid_fernet_key_is_rejected():
    with pytest.raises(ValueError, match="GOOGLE_TOKEN_ENCRYPTION_KEY"):
        encrypt_refresh_token("refresh-secret", "invalid")


def test_enabled_classroom_requires_complete_configuration(base_settings):
    with pytest.raises(ValidationError):
        Settings(**base_settings, google_classroom_enabled=True)
```

- [x] **Step 2: Escrever os testes do state/PKCE**

```python
def test_oauth_context_is_bound_to_state_and_user():
    context = create_oauth_context(USER_ID, SECRET, now=NOW)
    assert validate_oauth_context(
        context.cookie, context.state, USER_ID, SECRET, now=NOW
    ) == context.verifier
    with pytest.raises(InvalidOAuthState):
        validate_oauth_context(context.cookie, "different", USER_ID, SECRET, now=NOW)
    with pytest.raises(InvalidOAuthState):
        validate_oauth_context(context.cookie, context.state, OTHER_USER_ID, SECRET, now=NOW)


def test_oauth_context_expires_after_ten_minutes():
    context = create_oauth_context(USER_ID, SECRET, now=NOW)
    with pytest.raises(InvalidOAuthState):
        validate_oauth_context(
            context.cookie,
            context.state,
            USER_ID,
            SECRET,
            now=NOW + timedelta(minutes=11),
        )
```

- [x] **Step 3: Rodar os testes e confirmar RED**

Run: `.\.venv\Scripts\python.exe -m pytest tests\unit\test_classroom_crypto.py -q`

Expected: FAIL porque `app.integrations.google_classroom` ainda não existe.

- [x] **Step 4: Adicionar dependências e configurações mínimas**

Em `pyproject.toml`, adicionar ao runtime:

```toml
"cryptography>=46,<51",
"httpx>=0.28,<1",
```

Remover `httpx` da lista `dev` para evitar duplicação. Em `Settings`, adicionar campos e validação:

```python
google_classroom_enabled: bool = False
google_client_id: str | None = None
google_client_secret: str | None = None
google_oauth_redirect_uri: str = (
    "http://127.0.0.1:8000/api/integrations/classroom/callback"
)
google_token_encryption_key: str | None = None

if self.google_classroom_enabled:
    required = (
        self.google_client_id,
        self.google_client_secret,
        self.google_token_encryption_key,
    )
    if not all(required):
        raise ValueError("A configuração do Google Classroom está incompleta.")
if self.environment.casefold() == "production" and self.google_classroom_enabled:
    if not self.google_oauth_redirect_uri.startswith("https://"):
        raise ValueError("GOOGLE_OAUTH_REDIRECT_URI deve usar HTTPS em produção.")
```

- [x] **Step 5: Implementar Fernet e OAuthContext**

`crypto.py` deve converter erros de chave ou token em `ValueError` sem incluir valores secretos. `oauth.py` deve gerar verifier com `secrets.token_urlsafe(64)`, challenge com SHA-256 base64url sem padding e cookie JWT com `sub`, `state`, `verifier`, `aud`, `iat` e `exp=10 minutos`.

- [x] **Step 6: Rodar testes GREEN e suíte de segurança existente**

Run: `.\.venv\Scripts\python.exe -m pytest tests\unit\test_classroom_crypto.py tests\unit\test_security.py -q`

Expected: PASS.

- [x] **Step 7: Revisar o checkpoint**

Run: `git diff --check -- pyproject.toml .env.example app/core/config.py app/integrations tests/unit/test_classroom_crypto.py tests/conftest.py`

Expected: saída vazia; nenhum segredo real no diff.

---

### Task 2: Schema privado, modelos e repositório

**Files:**
- Create: `app/models/classroom.py`
- Create: `app/repositories/classroom.py`
- Create: `alembic/versions/20260903_0002_google_classroom.py`
- Modify: `app/models/__init__.py`
- Modify: `app/models/user.py`
- Modify: `app/models/subject.py`
- Modify: `app/models/task.py`
- Modify: `alembic/env.py`
- Modify: `tests/conftest.py`
- Modify: `tests/unit/test_model_metadata.py`
- Create: `tests/repositories/test_classroom_repository.py`

**Interfaces:**
- Produces: `ClassroomConnection`, `ClassroomCourseLink`, `ClassroomTaskLink`.
- Produces: `ClassroomRepository.get_connection(db, user_id)`.
- Produces: `ClassroomRepository.upsert_connection(db, user_id, encrypted_refresh_token, granted_scopes)`.
- Produces: `get_course_link`, `create_course_link`, `get_task_link`, `create_task_link` com `db.flush()` e sem `commit()`.
- Consumes: modelos `User`, `Subject` e `AcademicTask` existentes.

- [ ] **Step 1: Expandir o teste de metadata antes dos modelos**

```python
assert set(Base.metadata.tables) == {
    "users",
    "password_reset_tokens",
    "subjects",
    "academic_tasks",
    "private.classroom_connections",
    "private.classroom_course_links",
    "private.classroom_task_links",
}
assert ClassroomConnection.__table__.schema == "private"
assert ClassroomCourseLink.__table__.schema == "private"
assert ClassroomTaskLink.__table__.schema == "private"
```

- [ ] **Step 2: Escrever testes de propriedade e unicidade do repositório**

```python
def test_repository_links_one_google_course_and_task_once(db_session, user_factory):
    user = user_factory()
    connection = ClassroomRepository.upsert_connection(
        db_session, user.id, "encrypted", SCOPES
    )
    subject = Subject(user_id=user.id, name="Python", workload_hours=1)
    db_session.add(subject)
    db_session.flush()
    first = ClassroomRepository.create_course_link(
        db_session, connection.id, subject.id, "course-1", "ACTIVE"
    )
    assert ClassroomRepository.get_course_link(
        db_session, connection.id, "course-1"
    ).id == first.id


def test_linked_entities_expose_only_safe_source_metadata(linked_task):
    assert linked_task.source == "google_classroom"
    assert linked_task.external_url == "https://classroom.google.com/c/example"
```

- [ ] **Step 3: Rodar testes e confirmar RED**

Run: `.\.venv\Scripts\python.exe -m pytest tests\unit\test_model_metadata.py tests\repositories\test_classroom_repository.py -q`

Expected: FAIL porque os três modelos e o repositório não existem.

- [ ] **Step 4: Implementar modelos e relações um-para-um**

Usar `__table_args__ = {"schema": "private"}`, UUIDs, cascatas do spec e relações `uselist=False`. Adicionar propriedades seguras:

```python
@property
def source(self) -> str:
    return "google_classroom" if self.classroom_link else "local"

@property
def external_url(self) -> str | None:
    return self.classroom_link.alternate_link if self.classroom_link else None
```

Em `Subject`, `external_url` permanece `None`; o selo depende apenas de `source`.

- [ ] **Step 5: Implementar repositório sem commits internos**

Cada método de criação adiciona o modelo e usa `db.flush()`. `delete_connection()` remove somente a conexão e seus links por cascata; nunca remove `Subject` ou `AcademicTask`.

- [ ] **Step 6: Criar migração reversível**

A migração deve executar, na ordem:

```python
op.execute("CREATE SCHEMA IF NOT EXISTS private")
# create_table(..., schema="private") para conexão, curso e tarefa
for table in (
    "classroom_connections",
    "classroom_course_links",
    "classroom_task_links",
):
    op.execute(f'ALTER TABLE private."{table}" ENABLE ROW LEVEL SECURITY')
```

Revogar `anon` e `authenticated` dentro de bloco `DO` apenas se os papéis existirem. O downgrade remove tabelas na ordem inversa e executa `DROP SCHEMA private` sem `CASCADE`.

- [ ] **Step 7: Atualizar limpeza dos testes**

Executar primeiro:

```sql
TRUNCATE TABLE
  private.classroom_task_links,
  private.classroom_course_links,
  private.classroom_connections,
  password_reset_tokens,
  academic_tasks,
  subjects,
  users
RESTART IDENTITY CASCADE
```

- [ ] **Step 8: Aplicar migração e confirmar GREEN**

Run: `.\.venv\Scripts\python.exe -m alembic upgrade head`

Run: `.\.venv\Scripts\python.exe -m pytest tests\unit\test_model_metadata.py tests\repositories\test_classroom_repository.py -q`

Expected: PASS.

- [ ] **Step 9: Provar reversibilidade no banco de teste**

Run: `.\.venv\Scripts\python.exe -m alembic downgrade -1`

Run: `.\.venv\Scripts\python.exe -m alembic upgrade head`

Expected: ambos exit code 0 e `alembic current` mostra `20260903_0002`.

---

### Task 3: Cliente OAuth e API REST do Google Classroom

**Files:**
- Create: `app/integrations/google_classroom/client.py`
- Create: `tests/unit/test_classroom_client.py`

**Interfaces:**
- Produces: `GoogleTokens(access_token: str, refresh_token: str | None, scopes: frozenset[str])`.
- Produces: `GoogleClassroomError(code: str, retryable: bool)` sem payload ou token.
- Produces: `GoogleClassroomClient.authorization_url(state, challenge) -> str`.
- Produces: `exchange_code(code, verifier) -> GoogleTokens`.
- Produces: `refresh_access_token(refresh_token) -> str`.
- Produces: `list_active_courses(access_token) -> list[dict]`.
- Produces: `list_published_coursework(access_token, course_id) -> list[dict]`.
- Produces: `list_my_submissions(access_token, course_id, coursework_id) -> list[dict]`.

- [ ] **Step 1: Escrever testes HTTP com MockTransport**

```python
def test_authorization_url_uses_exact_readonly_scopes(client):
    query = parse_qs(urlparse(client.authorization_url("state-1", "challenge-1")).query)
    assert query["scope"] == [
        "https://www.googleapis.com/auth/classroom.courses.readonly "
        "https://www.googleapis.com/auth/classroom.coursework.me.readonly"
    ]
    assert query["code_challenge_method"] == ["S256"]
    assert query["access_type"] == ["offline"]


def test_courses_are_paginated_until_next_page_token(client_with_transport):
    courses = client_with_transport.list_active_courses("access-token")
    assert [course["id"] for course in courses] == ["course-1", "course-2"]


def test_google_error_is_sanitized(client_returning_401):
    with pytest.raises(GoogleClassroomError) as captured:
        client_returning_401.list_active_courses("secret-access-token")
    assert captured.value.code == "google_unauthorized"
    assert "secret-access-token" not in str(captured.value)
```

- [ ] **Step 2: Rodar testes e confirmar RED**

Run: `.\.venv\Scripts\python.exe -m pytest tests\unit\test_classroom_client.py -q`

Expected: FAIL porque `GoogleClassroomClient` não existe.

- [ ] **Step 3: Implementar cliente com httpx.Client**

Usar endpoints fixos oficiais, timeout total de 15 segundos e `follow_redirects=False`. Codificar IDs de path com `quote(value, safe="")`. A paginação repete a requisição enquanto existir `nextPageToken`.

Parâmetros literais:

```python
COURSE_PARAMS = {"courseStates": "ACTIVE", "pageSize": 100}
COURSEWORK_PARAMS = {"courseWorkStates": "PUBLISHED", "pageSize": 100}
SUBMISSION_PARAMS = {"userId": "me", "pageSize": 100}
```

Mapear `401` para `google_unauthorized`, `403` para `google_access_blocked`, `429` e `5xx` para `google_temporarily_unavailable`; nunca incorporar o corpo remoto à mensagem da exceção.

- [ ] **Step 4: Rodar testes GREEN**

Run: `.\.venv\Scripts\python.exe -m pytest tests\unit\test_classroom_client.py -q`

Expected: PASS cobrindo paginação, token exchange, refresh e erros.

- [ ] **Step 5: Revisar o checkpoint**

Run: `git diff --check -- app/integrations/google_classroom/client.py tests/unit/test_classroom_client.py`

Expected: saída vazia e nenhum valor de fixture parecido com credencial real.

---

### Task 4: Sincronização transacional e idempotente

**Files:**
- Create: `app/integrations/google_classroom/sync.py`
- Create: `app/schemas/classroom.py`
- Create: `tests/unit/test_classroom_sync.py`
- Modify: `app/repositories/classroom.py`

**Interfaces:**
- Consumes: `GoogleClassroomClient`, `ClassroomRepository`, token cifrado e `Session`.
- Produces: `ClassroomSyncService.sync(db: Session, user_id: UUID, client: ClassroomGateway, encryption_key: str) -> ClassroomSyncResult`.
- Produces: `ClassroomSyncResult(courses_created, courses_updated, tasks_created, tasks_updated, skipped_without_due_date, warnings)`.
- Produces: `map_submission_status(remote_state: str | None, local_status: TaskStatus) -> TaskStatus`.

- [ ] **Step 1: Escrever fixture de gateway completo**

```python
class FakeClassroomGateway:
    def refresh_access_token(self, refresh_token: str) -> str:
        assert refresh_token == "refresh-secret"
        return "memory-only-access"

    def list_active_courses(self, access_token: str) -> list[dict]:
        return [{"id": "course-1", "name": "Python Aplicado", "courseState": "ACTIVE"}]

    def list_published_coursework(self, access_token: str, course_id: str) -> list[dict]:
        return [
            {
                "id": "work-1",
                "title": "Projeto final",
                "description": "Entregar análise",
                "dueDate": {"year": 2026, "month": 9, "day": 15},
                "alternateLink": "https://classroom.google.com/c/example",
                "updateTime": "2026-09-03T12:00:00Z",
            },
            {"id": "work-no-date", "title": "Leitura livre"},
        ]

    def list_my_submissions(self, access_token: str, course_id: str, coursework_id: str):
        return [{"id": "submission-1", "state": "CREATED"}]
```

- [ ] **Step 2: Escrever testes de regras e idempotência**

```python
@pytest.mark.parametrize(
    ("remote", "local", "expected"),
    [
        ("TURNED_IN", TaskStatus.PENDING, TaskStatus.COMPLETED),
        ("RETURNED", TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED),
        ("RECLAIMED", TaskStatus.COMPLETED, TaskStatus.PENDING),
        ("CREATED", TaskStatus.IN_PROGRESS, TaskStatus.IN_PROGRESS),
        ("NEW", TaskStatus.PENDING, TaskStatus.PENDING),
    ],
)
def test_submission_state_mapping(remote, local, expected):
    assert map_submission_status(remote, local) == expected


def test_repeated_sync_creates_records_only_once(configured_connection, db_session):
    first = service.sync(db_session, USER_ID, FakeClassroomGateway(), KEY)
    second = service.sync(db_session, USER_ID, FakeClassroomGateway(), KEY)
    assert first.model_dump() == {
        "courses_created": 1,
        "courses_updated": 0,
        "tasks_created": 1,
        "tasks_updated": 0,
        "skipped_without_due_date": 1,
        "warnings": [],
    }
    assert second.courses_created == 0
    assert second.tasks_created == 0
    assert db_session.scalar(select(func.count(Subject.id))) == 1
    assert db_session.scalar(select(func.count(AcademicTask.id))) == 1
```

- [ ] **Step 3: Rodar testes e confirmar RED**

Run: `.\.venv\Scripts\python.exe -m pytest tests\unit\test_classroom_sync.py -q`

Expected: FAIL porque o serviço e `map_submission_status` não existem.

- [ ] **Step 4: Implementar schemas e sincronização**

O serviço deve:

1. buscar a conexão do usuário;
2. decifrar o refresh token;
3. obter access token em memória;
4. upsert de cursos por `(connection_id, classroom_course_id)`;
5. upsert de atividades com prazo por `(course_link_id, classroom_coursework_id)`;
6. aplicar o estado da própria entrega;
7. preencher `last_synced_at` e limpar `last_error_code`;
8. executar um único `db.commit()` ao final;
9. executar `db.rollback()` e persistir apenas o código sanitizado em uma nova transação quando houver falha.

Converter `dueDate` diretamente para `date(year, month, day)`. Atividade sem `dueDate` incrementa `skipped_without_due_date` sem criar registro.

- [ ] **Step 5: Adicionar teste de atualização da fonte**

Após o primeiro sync, alterar o fixture para `title="Projeto final revisado"`, prazo `2026-09-20` e estado `TURNED_IN`. Confirmar `tasks_updated == 1`, título/prazo atualizados, status `completed` e `completed_at` preenchido.

- [ ] **Step 6: Rodar GREEN e verificar rollback**

Run: `.\.venv\Scripts\python.exe -m pytest tests\unit\test_classroom_sync.py -q`

Expected: PASS, incluindo um teste em que o gateway falha no segundo curso e nenhuma importação parcial permanece.

---

### Task 5: API OAuth, status, sincronização e desconexão

**Files:**
- Create: `app/api/classroom.py`
- Create: `tests/api/test_classroom_integration.py`
- Modify: `app/main.py`
- Modify: `app/schemas/classroom.py`

**Interfaces:**
- Produces: `get_classroom_client() -> GoogleClassroomClient`, substituível em `dependency_overrides`.
- Produces: endpoints `GET status`, `GET authorize`, `GET callback`, `POST sync`, `DELETE connection` sob `/api/integrations/classroom`.
- Consumes: sessão EduTrack, OAuthContext, crypto, repository e sync service.

- [ ] **Step 1: Escrever testes de status e autenticação**

```python
def test_classroom_status_requires_edutrack_session(client):
    assert client.get("/api/integrations/classroom").status_code == 401


def test_disabled_integration_returns_available_false(authenticated_client):
    response = authenticated_client.get("/api/integrations/classroom")
    assert response.status_code == 200
    assert response.json() == {
        "available": False,
        "connected": False,
        "last_synced_at": None,
        "last_error_code": None,
    }
```

- [ ] **Step 2: Escrever testes do redirect e callback**

```python
def test_authorize_sets_secure_context_cookie_and_redirects_to_google(
    configured_client, authenticated_client
):
    response = authenticated_client.get(
        "/api/integrations/classroom/authorize", follow_redirects=False
    )
    assert response.status_code == 307
    assert response.headers["location"].startswith("https://accounts.google.com/")
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie
    assert "refresh" not in cookie


def test_callback_rejects_wrong_state_without_storing_token(
    authenticated_client, db_session
):
    response = authenticated_client.get(
        "/api/integrations/classroom/callback?code=code-1&state=wrong",
        follow_redirects=False,
    )
    assert response.status_code == 307
    assert "classroom=invalid_state" in response.headers["location"]
    assert ClassroomRepository.get_connection(db_session, USER_ID) is None
```

- [ ] **Step 3: Escrever testes de sync e desconexão**

Injetar gateway fake pela dependência. Confirmar `POST sync` retorna contagens literais, `DELETE` retorna 204, a conexão desaparece e `Subject`/`AcademicTask` continuam existentes.

- [ ] **Step 4: Rodar testes e confirmar RED**

Run: `.\.venv\Scripts\python.exe -m pytest tests\api\test_classroom_integration.py -q`

Expected: FAIL com 404 porque o router ainda não está registrado.

- [ ] **Step 5: Implementar router e cookies**

Usar cookie `edutrack_google_oauth` com `max_age=600`, `httponly=True`, `samesite="lax"`, `secure=settings.cookie_secure`, `path="/api/integrations/classroom"`. Apagar o cookie em todos os caminhos do callback.

O callback deve redirecionar apenas para valores constantes:

```python
CALLBACK_TARGETS = {
    "connected": "/?classroom=connected#integrations",
    "access_denied": "/?classroom=access_denied#integrations",
    "invalid_state": "/?classroom=invalid_state#integrations",
    "access_blocked": "/?classroom=access_blocked#integrations",
    "failed": "/?classroom=failed#integrations",
}
```

Não aceitar destino de redirect fornecido pelo cliente.

- [ ] **Step 6: Rodar GREEN e teste de vazamento**

Run: `.\.venv\Scripts\python.exe -m pytest tests\api\test_classroom_integration.py tests\api\test_auth.py -q`

Expected: PASS e nenhum response body/header contém os tokens das fixtures.

---

### Task 6: Metadados de origem nas APIs de disciplinas e tarefas

**Files:**
- Modify: `app/repositories/subjects.py`
- Modify: `app/repositories/tasks.py`
- Modify: `app/schemas/subject.py`
- Modify: `app/schemas/task.py`
- Modify: `tests/api/test_subjects.py`
- Modify: `tests/api/test_tasks.py`

**Interfaces:**
- Produces em `SubjectOutput`: `source: Literal["local", "google_classroom"] = "local"`.
- Produces em `TaskOutput`: `source: Literal["local", "google_classroom"] = "local"` e `external_url: HttpUrl | None = None`.
- Consumes: relações `classroom_link` da Task 2.

- [ ] **Step 1: Escrever testes dos contratos JSON**

```python
def test_local_task_has_safe_source_metadata(authenticated_client, task_factory):
    task = task_factory()
    payload = authenticated_client.get(f"/api/tasks/{task.id}").json()
    assert payload["source"] == "local"
    assert payload["external_url"] is None


def test_classroom_task_exposes_link_but_never_connection_secret(
    authenticated_client, linked_task
):
    payload = authenticated_client.get(f"/api/tasks/{linked_task.id}").json()
    assert payload["source"] == "google_classroom"
    assert payload["external_url"] == "https://classroom.google.com/c/example"
    assert "refresh" not in json.dumps(payload).lower()
```

- [ ] **Step 2: Rodar testes e confirmar RED**

Run: `.\.venv\Scripts\python.exe -m pytest tests\api\test_subjects.py tests\api\test_tasks.py -q`

Expected: FAIL porque os campos ainda não existem.

- [ ] **Step 3: Adicionar campos e eager loading**

Adicionar `selectinload(Subject.classroom_link)` nas consultas de disciplinas e `joinedload(AcademicTask.classroom_link)` nas consultas de tarefas, preservando o eager load atual de `subject`.

- [ ] **Step 4: Rodar GREEN**

Run: `.\.venv\Scripts\python.exe -m pytest tests\api\test_subjects.py tests\api\test_tasks.py -q`

Expected: PASS sem alterar os campos existentes.

---

### Task 7: Tela de Integrações e selos Google Classroom

**Files:**
- Create: `app/static/js/integrations.js`
- Create: `app/static/css/integrations.css`
- Modify: `app/static/index.html`
- Modify: `app/static/js/app.js`
- Modify: `app/static/js/subjects.js`
- Modify: `app/static/js/tasks.js`
- Modify: `tests/api/test_frontend.py`
- Modify: `tests/e2e/test_auth_flow.py`

**Interfaces:**
- Produces: `renderIntegrations()`, registrado como route `integrations`.
- Consumes: `GET/POST/DELETE /api/integrations/classroom`.
- Consumes: `subject.source`, `task.source` e `task.external_url`.

- [ ] **Step 1: Escrever teste E2E desconectado antes da UI**

```python
page.get_by_role("link", name="Integrações", exact=True).click()
expect(page.get_by_role("heading", name="Integrações")).to_be_visible()
classroom = page.locator("#classroom-integration")
expect(classroom.get_by_role("heading", name="Google Classroom")).to_be_visible()
expect(classroom.get_by_role("button", name="Conectar Google Classroom")).to_be_visible()
```

- [ ] **Step 2: Escrever teste E2E conectado com rota fake interna**

Interceptar somente endpoints internos `/api/integrations/classroom`, nunca URLs do Google. Retornar status conectado e resultado de sync; confirmar “Sincronização concluída”, as cinco contagens e o botão “Sincronizar agora”.

- [ ] **Step 3: Escrever teste de selos e link seguro**

Com fixture persistida de vínculo, abrir Disciplinas e Tarefas, confirmar selo “Google Classroom” e link `target="_blank"` com `rel="noopener noreferrer"` apontando exatamente para o `alternateLink`.

- [ ] **Step 4: Rodar testes e confirmar RED**

Run: `.\.venv\Scripts\python.exe -m pytest tests\api\test_frontend.py tests\e2e\test_auth_flow.py -q`

Expected: FAIL porque a rota, o cartão e os selos não existem.

- [ ] **Step 5: Implementar shell e navegação**

Adicionar link lateral com ícone `ph-plugs-connected`, section `#integrations-view`, stylesheet versionado e módulo JS. Atualizar `routes` e o título de documento em `app.js`:

```javascript
const routes = {
  dashboard: renderDashboard,
  agenda: renderAgenda,
  subjects: renderSubjects,
  tasks: renderTasks,
  integrations: renderIntegrations,
};
```

- [ ] **Step 6: Implementar os quatro estados da integração**

`renderIntegrations()` mostra loading, unavailable, disconnected, connected ou action-required. “Conectar” navega para `/api/integrations/classroom/authorize`; “Sincronizar” usa `request(..., {method: "POST"})`; “Desconectar” usa `confirmAction` e DELETE.

Ler `classroom` de `location.search`, mostrar toast com mapa fechado de mensagens e limpar apenas esse parâmetro por `history.replaceState`, preservando hash e outros parâmetros.

- [ ] **Step 7: Implementar selos sem duplicar lógica**

Adicionar helper pequeno em cada módulo existente:

```javascript
const classroomBadge = source => source === "google_classroom"
  ? '<span class="classroom-badge"><i class="ph ph-google-logo" aria-hidden="true"></i>Google Classroom</span>'
  : "";
```

Em tarefas vinculadas, renderizar o link apenas quando `external_url` existir e validar no frontend que começa com `https://classroom.google.com/`; a API continua sendo a autoridade do valor.

- [ ] **Step 8: Implementar CSS responsivo e reduced motion**

Reutilizar `--surface`, `--border`, `--primary`, `--success`, `--danger` e raios existentes; não usar gradientes. Em 390 px, ações ocupam a largura, cards ficam em uma coluna e `document.documentElement.scrollWidth <= window.innerWidth`.

- [ ] **Step 9: Rodar GREEN e gerar capturas**

Run: `.\.venv\Scripts\python.exe -m pytest tests\api\test_frontend.py tests\e2e\test_auth_flow.py -q`

Expected: PASS e capturas `tmp/ui/integrations-desktop.png` e `tmp/ui/integrations-mobile.png`.

---

### Task 8: Documentação, segurança e verificação integrada

**Files:**
- Modify: `README.md`
- Verify: todos os arquivos anteriores

**Interfaces:**
- Consumes: integração completa das Tasks 1–7.
- Produces: instruções reproduzíveis para Google Cloud local e produção.

- [ ] **Step 1: Documentar configuração real**

Adicionar ao README:

1. criar projeto no Google Cloud;
2. habilitar Google Classroom API;
3. configurar tela de consentimento External em modo Testing;
4. adicionar o usuário Google pessoal como test user;
5. cadastrar redirect local literal;
6. gerar chave com `.\.venv\Scripts\python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`;
7. preencher `.env` e reiniciar o servidor;
8. explicar o possível bloqueio administrativo da conta institucional.

- [ ] **Step 2: Rodar suíte completa**

Run: `.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q`

Expected: todos os testes PASS; a única advertência aceitável é a depreciação já existente de `fastapi.testclient`/Starlette.

- [ ] **Step 3: Rodar lint e sintaxe frontend**

Run: `.\.venv\Scripts\python.exe -m ruff check --no-cache app scripts tests alembic`

Run: `node --check app/static/js/integrations.js`

Run: `node --check app/static/js/app.js`

Run: `node --check app/static/js/subjects.js`

Run: `node --check app/static/js/tasks.js`

Expected: todos exit code 0.

- [ ] **Step 4: Revalidar migração do zero**

No cluster de teste vazio, executar `alembic upgrade head`, `alembic downgrade -1`, `alembic upgrade head` e `alembic current`. Confirmar revision `20260903_0002`.

- [ ] **Step 5: Fazer auditoria de segredo e diff**

Run: `git diff --check`

Run: `git diff -- . ':!README.md' | rg -n "ya29\.|1//|refresh-secret|client_secret.*[^=]$|GOOGLE_TOKEN_ENCRYPTION_KEY=.+"`

Expected: `git diff --check` sem erros e a busca sem credenciais reais; valores literais de teste permanecem apenas em fixtures explicitamente falsas.

- [ ] **Step 6: Teste real opcional e controlado**

Com credenciais fornecidas pelo usuário em `.env`, conectar uma conta pessoal de teste, importar uma turma de teste, repetir o sincronismo e confirmar zero duplicações. Não executar esta etapa com conta institucional nem publicar a tela OAuth sem solicitação explícita.

- [ ] **Step 7: Revisar status final sem commit automático**

Run: `git status --short`

Listar separadamente arquivos da integração e alterações anteriores já existentes. Só criar commit/push após pedido explícito do usuário.

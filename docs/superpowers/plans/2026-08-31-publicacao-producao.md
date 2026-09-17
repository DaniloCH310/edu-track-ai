# Publicação em Produção Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tornar o EduTrack publicável no Render com Supabase, testes automáticos e operação segura documentada.

**Architecture:** O FastAPI continuará servindo o frontend e a API no mesmo serviço Render. A aplicação receberá a conexão PostgreSQL por `DATABASE_URL` como segredo do ambiente; o workflow GitHub Actions usará um PostgreSQL efêmero para validar as migrações, testes e lint. Backups permanecem no serviço gerenciado do Supabase e o procedimento de restauração fica documentado.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, Alembic, PostgreSQL 16, Supabase, Render Blueprints e GitHub Actions.

**Spec:** Decisão aprovada pelo usuário em 2026-08-31: Render + Supabase configurado pelo responsável pela instalação, CI, backups e nenhum segredo no repositório.

## Global Constraints

- Nunca versionar senha do banco, senha Gmail, `JWT_SECRET` ou URL de produção.
- Usar conexão SSL e o pooler de sessão do Supabase para o container Render em rede IPv4.
- Manter `README.md` fora do escopo por possuir alteração local do usuário.
- Não alterar dados nem esquema do projeto Supabase durante esta preparação.

---

### Task 1: Validar as proteções de configuração de produção

**Files:**

- Create: `tests/unit/test_production_config.py`
- Modify: `app/core/config.py`

**Interfaces:**

- Produces: `Settings()` recusa cookies inseguros e URL não HTTPS em produção.

- [x] **Step 1: Write the failing tests**

```python
def test_production_rejects_insecure_cookie():
    with pytest.raises(ValidationError):
        Settings(environment="production", cookie_secure=False, **REQUIRED)
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_production_config.py -v`
Expected: FAIL because production settings are accepted.

- [x] **Step 3: Write minimal implementation**

Add a model validator that requires `COOKIE_SECURE=true` and an HTTPS `FRONTEND_URL` in production.

- [x] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_production_config.py -v`
Expected: PASS.

### Task 2: Adicionar configuração declarativa de deploy e CI

**Files:**

- Create: `render.yaml`
- Create: `.github/workflows/ci.yml`
- Create: `.env.production.example`

**Interfaces:**

- Produces: blueprint Render com health check `/api/health` e workflow executável pelo GitHub.

- [x] **Step 1: Write configuration contracts**

Document and encode the secret keys required by the service and the CI database contract.

- [x] **Step 2: Validate configuration syntax and required keys**

Run a Python check that parses both YAML files and compares keys in `render.yaml` with `.env.production.example`.

- [x] **Step 3: Add minimal configuration**

Set `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT` as the Render start command. Configure GitHub Actions with a PostgreSQL 16 service, migrations, pytest and ruff.

- [x] **Step 4: Re-run configuration validation**

Expected: valid YAML and no secret value committed.

### Task 3: Documentar operação, backup e restauração

**Files:**

- Create: `docs/production.md`

**Interfaces:**

- Produces: instruções para conectar o projeto Supabase, criar o serviço Render, configurar os segredos, validar o deploy e restaurar um backup.

- [x] **Step 1: Document production runbook**

Include exact secret names, connection selection, deployment procedure, health check, automated test behavior, backup verification and rollback.

- [x] **Step 2: Review security constraints**

Confirm the document never includes concrete credentials and does not instruct exposing Supabase keys in browser code.

### Task 4: Verificar e versionar somente os arquivos do escopo

**Files:**

- Modify: files created in Tasks 1-3 only.

- [x] **Step 1: Run focused and full tests**

Run the new config test, all pytest tests and Ruff.

- [x] **Step 2: Inspect diff**

Confirm `README.md` remains untouched and no credential, `.env` or database file is staged.

- [ ] **Step 3: Commit**

```bash
git add app/core/config.py tests/unit/test_production_config.py render.yaml .github/workflows/ci.yml .env.production.example docs/production.md docs/superpowers/plans/2026-08-31-publicacao-producao.md
git commit -m "chore: prepara publicação em produção"
```

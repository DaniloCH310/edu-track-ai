# Agenda Semanal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar uma agenda semanal responsiva que permita consultar e concluir tarefas pelos seus prazos.

**Architecture:** Um módulo de frontend calcula o intervalo semanal e renderiza tarefas retornadas pelo endpoint autenticado existente. A alteração de status reutiliza `PATCH /api/tasks/{id}/status` e emite o evento de atualização já consumido pelo dashboard.

**Tech Stack:** HTML5, CSS3, JavaScript ES modules, FastAPI existente, Playwright e pytest.

**Spec:** `docs/superpowers/specs/2026-08-31-agenda-semanal-design.md`

## Global Constraints

- Não criar tabelas, migrações ou novas dependências.
- Preservar o isolamento por usuário assegurado pela API de tarefas.
- Usar textos e rótulos acessíveis em português.
- Validar desktop e viewport de 390 px com Playwright.

---

### Task 1: Cobertura E2E da agenda

**Files:**
- Modify: `tests/e2e/test_auth_flow.py`
- Test: `tests/e2e/test_auth_flow.py`

**Interfaces:**
- Consumes: fluxo existente de cadastro, disciplina e criação de tarefa.
- Produces: evidência de que a rota Agenda exibe e conclui a tarefa criada.

- [ ] **Step 1: Write the failing test**

```python
page.get_by_role("link", name="Agenda", exact=True).click()
expect(page.get_by_role("heading", name="Agenda semanal")).to_be_visible()
expect(page.get_by_text("Finalizar exercício", exact=True)).to_be_visible()
page.get_by_label("Status de Finalizar exercício na agenda").select_option("completed")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/e2e/test_auth_flow.py::test_student_sees_and_updates_task_in_weekly_agenda -v`

- [ ] **Step 3: Implement the smallest UI and module changes**

Create `app/static/js/agenda.js`; add the route, view markup and responsive styles.

- [ ] **Step 4: Run the E2E test to verify it passes**

Run: `python -m pytest tests/e2e/test_auth_flow.py::test_student_sees_and_updates_task_in_weekly_agenda -v`

### Task 2: Integração e regressão

**Files:**
- Modify: `app/static/js/app.js`
- Modify: `app/static/js/tasks.js`
- Test: `tests/e2e/test_auth_flow.py`

**Interfaces:**
- Consumes: evento global `data:changed`.
- Produces: atualização coerente de dashboard, tarefas e agenda após mudança de status.

- [ ] **Step 1: Add the responsive acceptance assertion**

```python
page.set_viewport_size({"width": 390, "height": 844})
assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
```

- [ ] **Step 2: Run the focused test and confirm the new assertion fails before CSS support**

Run: `python -m pytest tests/e2e/test_auth_flow.py::test_student_sees_and_updates_task_in_weekly_agenda -v`

- [ ] **Step 3: Add responsive agenda styles and event refresh wiring**

Render each day as a stacked section on narrow screens and refresh the active Agenda route on `data:changed`.

- [ ] **Step 4: Run focused and complete verification**

Run: `python -m pytest -p no:cacheprovider; python -m ruff check --no-cache app scripts tests alembic`

- [ ] **Step 5: Commit**

```bash
git add app/static docs tests/e2e/test_auth_flow.py
git commit -m "feat: adiciona agenda semanal"
```

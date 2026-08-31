# Plano de Estudo Inteligente Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Recomendar ao estudante a tarefa mais importante do momento no dashboard.

**Architecture:** A regra pura no serviço do dashboard deriva progresso por disciplina e classifica tarefas não concluídas. O contrato existente recebe um campo opcional; o frontend renderiza o cartão a partir dele.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy, JavaScript ES modules, pytest.

**Spec:** `docs/superpowers/specs/2026-08-31-plano-estudo-inteligente-design.md`

## Global Constraints

- Nenhuma dependência de IA generativa, tabela ou migração.
- Recomendação explicável em português e isolada ao usuário autenticado.
- Testes primeiro para regra de prioridade e estado sem tarefas.

---

### Task 1: Regra e contrato do dashboard

**Files:**
- Modify: `tests/unit/test_dashboard_service.py`
- Modify: `app/services/dashboard.py`
- Modify: `app/schemas/dashboard.py`

**Interfaces:**
- Produces: `DashboardOutput.recommended_task: StudyRecommendationOutput | None`.

- [ ] **Step 1: Write failing unit tests**

```python
assert dashboard.recommended_task.title == "Atrasada"
assert dashboard.recommended_task.priority == "urgent"
assert "atrasada" in dashboard.recommended_task.reason.casefold()
```

- [ ] **Step 2: Run the targeted test and confirm it fails**

Run: `python -m pytest tests/unit/test_dashboard_service.py -v`

- [ ] **Step 3: Implement the minimal ranking and output schema**

Use a tuple of urgency, subject progress, due date and title to select one pending task.

- [ ] **Step 4: Run the targeted test and confirm it passes**

Run: `python -m pytest tests/unit/test_dashboard_service.py -v`

### Task 2: Cartão do dashboard

**Files:**
- Modify: `app/static/js/dashboard.js`
- Modify: `app/static/css/app.css`

**Interfaces:**
- Consumes: `DashboardOutput.recommended_task`.
- Produces: cartão de recomendação com link para `#agenda`.

- [ ] **Step 1: Render the recommendation and empty state**

- [ ] **Step 2: Run frontend and E2E regression checks**

Run: `python -m pytest tests/api/test_dashboard.py tests/api/test_frontend.py tests/e2e/test_auth_flow.py -v`

- [ ] **Step 3: Commit**

```bash
git add app docs tests
git commit -m "feat: adiciona plano de estudo inteligente"
```

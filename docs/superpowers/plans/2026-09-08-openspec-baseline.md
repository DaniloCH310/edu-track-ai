# OpenSpec Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Registrar em OpenSpec as capacidades efetivamente entregues pelo EduTrack e definir o fluxo para evoluções futuras.

**Architecture:** A base canônica fica em `openspec/specs`, dividida por capacidade de produto. `openspec/project.md` registra decisões transversais e `openspec/changes` padroniza propostas futuras, sem mover nem invalidar os documentos históricos de design.

**Tech Stack:** Markdown, Git, FastAPI, PostgreSQL, HTML/CSS/JavaScript.

**Spec:** `openspec/project.md` e `openspec/specs/*/spec.md`

## Global Constraints

- A especificação deve descrever apenas comportamentos já presentes no FastAPI atual servido por `app/main.py`.
- `app.py` na raiz é legado e não deve ser tratado como aplicação de referência.
- Nenhum segredo, token, dado pessoal ou conteúdo de `.env` entra na documentação.
- A integração Google Classroom continua opcional, somente leitura e sujeita à política da instituição.

---

### Task 1: Estabelecer convenção OpenSpec

**Files:**
- Create: `openspec/README.md`
- Create: `openspec/project.md`
- Create: `openspec/changes/README.md`

**Interfaces:**
- Consumes: `README.md` e documentos históricos em `docs/superpowers/specs/`.
- Produces: uma estrutura canônica de capacidades e mudanças futuras.

- [x] **Step 1: Mapear a aplicação de referência**

Ler `README.md`, `app/main.py` e os documentos de design existentes para identificar a arquitetura atual, os comandos de operação e a distinção do protótipo Streamlit legado.

- [x] **Step 2: Criar o contexto do projeto**

Documentar propósito, stack, comandos Windows, convenções de produto, restrições de segurança e evoluções ainda não entregues em `openspec/project.md`.

- [x] **Step 3: Criar o fluxo de mudança**

Registrar que cada evolução começa em `openspec/changes/<identificador>/` com proposta, tarefas e deltas de spec; após aceite, a regra entra no spec canônico.

### Task 2: Especificar as capacidades entregues

**Files:**
- Create: `openspec/specs/authentication-and-account/spec.md`
- Create: `openspec/specs/academic-organization/spec.md`
- Create: `openspec/specs/campus-dashboard/spec.md`
- Create: `openspec/specs/weekly-agenda-and-study-plan/spec.md`
- Create: `openspec/specs/google-classroom-integration/spec.md`
- Create: `openspec/specs/delivery-and-portability/spec.md`

**Interfaces:**
- Consumes: rotas FastAPI, serviços de dashboard e módulos JavaScript atuais.
- Produces: requisitos normativos com cenários verificáveis em português.

- [x] **Step 1: Registrar conta e organização acadêmica**

Especificar autenticação, recuperação de senha, disciplinas, tarefas, status e isolamento por usuário.

- [x] **Step 2: Registrar a experiência de Campus e agenda**

Especificar Campus como dashboard vigente, cálculo de prioridade, rota semanal, resumo humano e atualização de status entre telas.

- [x] **Step 3: Registrar integração e portabilidade**

Especificar OAuth somente leitura, limites de políticas institucionais, importação idempotente, atalhos `.cmd`, diagnóstico de versão e proteção de dados locais.

### Task 3: Revisar o artefato

**Files:**
- Verify: `openspec/**/*.md`

**Interfaces:**
- Consumes: todos os arquivos criados em `openspec/`.
- Produces: documentação sem marcadores incompletos e sem erro de whitespace no Git.

- [x] **Step 1: Verificar a estrutura**

Run: `rg --files openspec | Sort-Object`

Expected: README, contexto, fluxo de mudanças e seis specs de capacidade.

- [x] **Step 2: Verificar qualidade textual e patch**

Run: `git diff --check; rg -n "TODO|TBD|implementar depois|fill in" openspec`

Expected: `git diff --check` sem saída e busca sem resultados.

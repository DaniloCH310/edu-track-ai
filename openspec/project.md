# EduTrack AI — Contexto do projeto

## Propósito

EduTrack AI é um MVP web para o estudante transformar disciplinas e prazos em uma jornada acadêmica clara. A experiência principal é o **Campus de aprendizagem**: cada disciplina se apresenta como um distrito/prédio em evolução e cada tarefa como uma missão com prazo.

## Estado de referência

Esta especificação descreve a aplicação FastAPI servida por `app/main.py`, com interface em `app/static/`. O arquivo `app.py` na raiz é um protótipo Streamlit legado e **não faz parte da aplicação atual**.

## Arquitetura

- Frontend: HTML, CSS e JavaScript modular sem framework, entregue pelo FastAPI.
- Backend: Python 3.12+, FastAPI, SQLAlchemy, Alembic e Uvicorn.
- Dados: PostgreSQL; no desenvolvimento, cluster portátil do projeto em `127.0.0.1:54329`.
- Segurança: autenticação própria, senhas com Argon2, sessão em cookie e segredos apenas em `.env`.
- Integração opcional: Google Classroom por OAuth 2.0 com PKCE e importação somente leitura.

## Comandos de operação

Em Windows 10/11, sem permissão administrativa:

```text
Instalar EduTrack.cmd
Iniciar EduTrack.cmd
Encerrar EduTrack.cmd
Diagnosticar EduTrack.cmd
```

Depois de iniciado, a aplicação responde em `http://127.0.0.1:8000`. A instalação procura Python 3.12 ou superior e prepara PostgreSQL portátil. O procedimento completo e a recuperação de falhas ficam no `README.md`.

## Convenções de produto

- Toda disciplina, tarefa, painel e integração é isolada pelo usuário autenticado.
- O status de tarefa é `pending`, `in_progress` ou `completed`.
- Progresso é a proporção arredondada de tarefas concluídas sobre o total; disciplina sem tarefa tem 0%.
- A semana acadêmica começa na segunda-feira e termina no domingo.
- A interface deve funcionar em desktop e em telas de 390 px sem rolagem horizontal.
- Textos da interface e da documentação de produto devem estar em português do Brasil.

## Restrições e segurança

- `.env`, `.venv`, `.data` e `.tools` não entram no Git.
- Credenciais Gmail, segredos OAuth e refresh tokens nunca podem aparecer em resposta da API, logs, commits ou interface.
- O Classroom é desabilitado por padrão e não bloqueia a inicialização quando não configurado.
- Dados importados do Classroom pertencem ao usuário e permanecem locais após desconectar; somente o vínculo e o token são removidos.
- O sistema não contorna políticas de uma instituição Google Workspace. Uma conta bloqueada exige liberação do administrador ou uso de uma conta autorizada.

## Fontes complementares

- `README.md`: instalação, operação local e configuração de serviços externos.
- `docs/superpowers/specs/`: decisões de design históricas.
- `docs/superpowers/plans/`: planos de implementação já executados.
- `tests/`: comportamento automatizado que deve permanecer válido.

## Evoluções que ainda não são requisitos entregues

- Publicação pública com Supabase e backup operacional validado.
- Notificações, tarefas recorrentes e integração com Google Calendar.
- Sincronização automática ou escrita no Google Classroom.
- Estimativa de tempo de estudo, relatórios PDF e colaboração entre estudantes.

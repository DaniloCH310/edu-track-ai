# Entrega final acadêmica - Tarefas 08 a 16

## Resumo

O EduTrack AI atende aos objetivos funcionais das Tarefas 08 a 16 com uma arquitetura alternativa permitida: FastAPI, SQLAlchemy, Alembic e PostgreSQL no backend, além de HTML, CSS e JavaScript no frontend. Xano e FlutterFlow não foram utilizados. As equivalências abaixo relacionam cada critério acadêmico a arquivos, testes e demonstrações reais do projeto.

## Matriz de conformidade

| Tarefa | Implementação equivalente | Evidência principal | Situação |
| --- | --- | --- | --- |
| 08 - OpenSpec | Propostas com requisito, cenário, tarefas, implementação, especificação canônica e arquivo histórico | `openspec/changes/archive/2026-11-17-add-subject-search/` e `openspec/specs/academic-organization/spec.md` | Concluída |
| 09 - Design e navegação | Dashboard, Disciplinas e Tarefas em HTML/CSS/JS, navegação por hash, design tokens e assets próprios | `app/static/index.html`, `app/static/js/app.js`, `app/static/css/tokens.css` e `app/static/assets/` | Concluída por equivalência |
| 10 - AGENTS.md | Arquitetura, escopo, segurança, testes, OpenSpec, Git e Graphify documentados | `AGENTS.md` e `docs/tarefa10-agents.md` | Concluída |
| 11 - Modelo de tarefas | Entidade SQLAlchemy, chave estrangeira de disciplina, migração Alembic, schemas e API | `app/models/task.py`, `alembic/versions/20260827_0001_initial_schema.py` e `app/api/tasks.py` | Concluída por equivalência |
| 12 - Cálculo de progresso | Regra Python compartilhada, interface JSON e tratamento de total zero e entradas inválidas | `app/services/progress.py`, `scripts/calculate_progress.py` e `tests/unit/test_calculate_progress.py` | Concluída |
| 13 - CRUD de disciplinas | POST, GET, PATCH e DELETE autenticados, com isolamento por usuário | `app/api/subjects.py`, `app/repositories/subjects.py` e testes da API | Concluída por equivalência |
| 14 - Busca acadêmica | `GET /api/subjects?query=...&overdue=true`, combinação AND, calendário de São Paulo e isolamento | `docs/task14-subject-search.md` e `tests/unit/test_subject_search.py` | Concluída |
| 15 - Relatório PDF | PDF semanal gerado em memória e baixado por endpoint autenticado | `app/services/reports.py`, `app/api/reports.py` e `tests/api/test_reports.py` | Concluída |
| 16 - Entrega final | Auditoria, validações, documentação, roteiro e branch final aberta para revisão | este documento, README, OpenSpec e Pull Request de `release/final-delivery` | Preparada; merge depende do professor |

## Reflexão sobre OpenSpec

O OpenSpec tornou explícitos o motivo, o comportamento esperado e os critérios de aceite de mudanças como o relatório semanal, o EDU IA e a busca acadêmica. As especificações canônicas permitem comparar o código atual com cenários observáveis, enquanto `openspec/changes/archive/` preserva o histórico das mudanças concluídas.

A regularização do OpenSpec ocorreu em etapas diferentes do desenvolvimento. Algumas capacidades foram documentadas retrospectivamente em 16/11/2026 para representar fielmente código que já existia; mudanças posteriores, como a busca acadêmica e o utilitário de progresso, possuem proposta, delta, tarefas, implementação, validação e arquivo produzidos no próprio ciclo da mudança. Essa distinção evita apresentar documentação posterior como planejamento original.

## Roteiro de demonstração

1. Abrir o login e autenticar com uma conta demonstrativa, sem exibir a senha.
2. Mostrar o Dashboard, os indicadores, o Campus e a próxima ação recomendada.
3. Abrir Disciplinas e demonstrar criação, consulta, edição e exclusão com dados demonstrativos.
4. Abrir Tarefas e demonstrar vínculo com disciplina, status, prazo, filtros e ordenação.
5. Abrir a Agenda e baixar o relatório semanal em PDF.
6. Abrir o Swagger em `/docs`, autenticar e mostrar os endpoints de disciplinas e tarefas.
7. Demonstrar `GET /api/subjects` sem filtros, com `query` e com `overdue=true`.
8. Executar `scripts.calculate_progress` com JSON e mostrar o resultado percentual.
9. Mostrar uma proposta arquivada e a especificação canônica correspondente no OpenSpec.
10. Mostrar o Pull Request final e o GitHub Actions aprovado, sem fazer merge.

## Validações exigidas antes da apresentação

- `git diff --check` sem erros;
- testes unitários de progresso, dashboard e busca aprovados;
- suíte completa aprovada no PostgreSQL descartável do GitHub Actions;
- Ruff aprovado;
- oito especificações OpenSpec aprovadas em modo estrito;
- relatório PDF aberto e visualmente legível;
- navegação Dashboard -> Disciplinas -> Tarefas validada no navegador;
- nenhum segredo, token ou captura com dados privados incluído no Git.

## Limitações e plano de contingência

- Google Classroom depende de credenciais OAuth e pode ser bloqueado pela política da instituição. A demonstração principal não depende dessa integração.
- EDU IA depende de uma chave Gemini válida e de disponibilidade externa. Se indisponível, a demonstração deve apresentar os testes e o tratamento de erro sem inventar resposta da IA.
- O envio real de recuperação de senha depende do SMTP. A resposta pública neutra e os testes simulados continuam demonstráveis sem e-mail externo.
- O PR da Tarefa 07 permanece independente enquanto aguarda revisão; sua ausência temporária na `main` não altera as funcionalidades.

## Checklist de submissão

- [ ] Enviar os PDFs de evidências das Tarefas 08 a 16 no Classroom.
- [ ] Anexar o PDF real gerado pelo EduTrack para a Tarefa 15.
- [ ] Informar o link do Pull Request final aberto.
- [ ] Informar o link do repositório e da documentação OpenSpec.
- [ ] Confirmar que os checks do Pull Request final estão aprovados.
- [ ] Manter o Pull Request final sem merge até a revisão do professor.
- [ ] Usar dados demonstrativos e ocultar credenciais durante a apresentação.

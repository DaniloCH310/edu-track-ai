# Tarefa 10 - Instruções para agentes de IA

## Objetivo

O arquivo `AGENTS.md` da raiz orienta agentes que trabalham no EduTrack AI sem presumir Xano ou FlutterFlow. As instruções registram a arquitetura FastAPI/PostgreSQL/HTML/CSS/JavaScript, a separação de camadas, o isolamento por usuário, a proteção do banco de testes, o fluxo OpenSpec, as validações e as convenções Git.

## Utilização verificável em 18/11/2026

Durante a preparação das Tarefas 08 a 16, o agente:

1. consultou o grafo do projeto antes de navegar pelo código, conforme a seção Graphify;
2. criou o worktree isolado `release/final-delivery` a partir de `origin/main`;
3. preservou as seis alterações locais de Graphify no checkout principal;
4. reaplicou somente o commit da busca acadêmica, sem incluir P4/P5;
5. criou propostas, deltas e tarefas OpenSpec para as novas mudanças;
6. executou testes unitários seguros, Ruff e validação estrita das oito especificações;
7. evitou banco local desconhecido e deixou o Pull Request final sem merge.

Esses passos demonstram uso real das instruções. O registro não afirma que a versão expandida do arquivo existia antes de 18/11/2026.

## Correspondência com a arquitetura alternativa

As orientações originais da disciplina citam Xano e FlutterFlow. No EduTrack, as responsabilidades equivalentes são atendidas por:

- FastAPI e SQLAlchemy para API e regras de negócio;
- PostgreSQL e Alembic para dados e versionamento do schema;
- HTML, CSS e JavaScript para interface e navegação;
- pytest, Ruff e GitHub Actions para verificação automatizada;
- OpenSpec para propostas, requisitos, cenários e histórico arquivado.

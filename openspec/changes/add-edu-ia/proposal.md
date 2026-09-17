# Proposta: adicionar EDU IA

## Problema

O EduTrack organiza a jornada de estudos, mas o estudante ainda precisa sair da plataforma para tirar dúvidas sobre uma disciplina ou começar uma tarefa.

## Objetivo

Adicionar o EDU IA como tutor contextual por texto, com Gemini configurável no servidor e histórico privado por usuário.

## Escopo

- Conversas gerais, por disciplina e por tarefa.
- Histórico, exclusão e isolamento por usuário.
- Gemini via API no backend, sem expor a chave ao navegador.
- Limites configuráveis de demonstração.

## Fora de escopo

- Anexos, PDFs, pesquisa na internet, streaming, edição automática de tarefas e envio de conteúdo ao Google Classroom.

## Impacto

Inclui duas tabelas PostgreSQL, uma migração Alembic, rotas autenticadas `/api/edu-ia` e configuração opcional no `.env`.

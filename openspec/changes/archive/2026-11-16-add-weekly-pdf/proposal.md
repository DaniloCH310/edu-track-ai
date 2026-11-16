# Relatório semanal em PDF

## Why

A Agenda apresenta o fechamento semanal, mas ainda não oferece um documento para download e apresentação acadêmica.

## What Changes

- Adicionar `GET /api/reports/generate`, autenticado, para a semana selecionada.
- Exportar resumo por prazo, conclusões registradas no período, pendências e progresso atual por disciplina.
- Adicionar botão de download na Agenda com indicação de processamento e erros.
- Gerar em memória, sem armazenar documentos pessoais no servidor, sem alterar tarefas.

## Impact

Novo serviço PDF com ReportLab, testes de conteúdo e isolamento por usuário. Não exige migração. O relatório é um retrato atual, não um histórico imutável de status.

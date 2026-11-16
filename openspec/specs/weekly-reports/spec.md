# Capacidade: relatório semanal em PDF

## Purpose
Permitir que o estudante baixe um retrato legível da semana selecionada, com entregas, conclusões e progresso acadêmico, preservando a privacidade dos dados e sem alterar seu planejamento.

## Requirements

### Requirement: Relatório semanal privado

O sistema SHALL oferecer `GET /api/reports/generate` somente a usuários autenticados, retornando um PDF para download com os dados do próprio usuário. O documento SHALL ser gerado em memória e enviado com cache desabilitado, sem modificar dados acadêmicos.

#### Scenario: Usuários possuem dados distintos

- **WHEN** um estudante gera o relatório
- **THEN** o PDF inclui somente suas disciplinas e tarefas, sem dados de outros usuários

### Requirement: Período e métricas explícitos

O relatório SHALL usar a semana de segunda a domingo que contém `week_start`, no fuso IANA `timezone` informado pelo navegador. Sem parâmetros, usa a semana atual de America/Sao_Paulo. SHALL distinguir tarefas com prazo na semana, conclusões registradas na semana e progresso atual de todas as disciplinas. Datas ou fusos inválidos SHALL retornar erro de validação.

#### Scenario: Tarefa concluída com prazo fora da semana

- **WHEN** uma tarefa atualmente concluída possui data de conclusão no período e prazo fora dele
- **THEN** ela aparece nas conclusões do período, sem aumentar a contagem de tarefas com prazo na semana

### Requirement: Download pela Agenda

A Agenda SHALL oferecer o botão Baixar relatório PDF para a semana selecionada, com estado de processamento e mensagem em caso de falha. O documento SHALL exibir período, identificação, geração, status atuais, pendências anteriores, próximas entregas e progresso por disciplina, com paginação legível.

#### Scenario: Semana vazia

- **WHEN** o usuário baixa uma semana sem tarefas
- **THEN** recebe um PDF válido com contagens zeradas e mensagens de ausência de tarefas

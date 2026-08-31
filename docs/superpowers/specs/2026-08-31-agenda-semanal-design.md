# Agenda semanal — design

## Objetivo

Permitir que o estudante veja, em uma única tela semanal, as tarefas do período, identifique prazos vencidos e altere o status sem sair da agenda.

## Escopo aprovado

- Nova rota `#agenda` na navegação principal.
- Sete colunas, de segunda a domingo, com controles para semana anterior, atual e próxima.
- Cada tarefa aparece no dia do seu prazo; tarefas vencidas recebem destaque visual.
- O seletor de status da tarefa usa o endpoint existente de atualização e atualiza dashboard, agenda e lista de tarefas.
- A agenda usa os dados já expostos por `GET /api/tasks`; não haverá nova tabela, migração ou dependência externa.

## Decisões

O frontend buscará as tarefas do usuário por prazo e filtrará somente os sete dias visíveis. Assim, o contrato autenticado e o isolamento de dados permanecem os mesmos. A semana começa na segunda-feira, e a navegação é feita por intervalos de sete dias.

Para telas pequenas, os dias serão empilhados, evitando uma tabela comprimida ou rolagem horizontal. Cada ação de status terá rótulo acessível e preservará a tarefa visível quando a atualização falhar.

## Critérios de aceite

1. A sidebar apresenta a opção Agenda e a rota abre a visão semanal.
2. Uma tarefa cadastrada para a semana aparece no dia correto, com título, disciplina e status.
3. A tarefa concluída na agenda atualiza o progresso no dashboard.
4. Dias sem tarefas apresentam uma indicação discreta.
5. Em 390 px não há rolagem horizontal.

## Fora de escopo

- Notificações por e-mail, tarefas recorrentes, integração Google Calendar e arrastar-e-soltar.

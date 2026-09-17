# Capacidade: dashboard Campus

## Propósito

Dar uma visão imediata da jornada acadêmica por meio de um Campus de aprendizagem, tornando visível o avanço por disciplina e a próxima ação mais útil.

## Requisitos

### Requirement: Campus é a experiência principal do dashboard

O dashboard DEVE usar a direção visual de Campus de aprendizagem, e não o protótipo antigo de ilhas. Disciplinas DEVEM ser apresentadas como áreas/prédios em evolução, com cor e percentual de progresso.

#### Scenario: Usuário abre o dashboard com disciplinas

- **WHEN** o dashboard é carregado para um usuário com disciplinas
- **THEN** o Campus mostra o progresso individual e geral de forma compreensível

### Requirement: Indicadores refletem tarefas reais

O dashboard DEVE apresentar total de disciplinas, progresso geral, entregas nos próximos três dias e tarefas em atraso, calculados somente a partir dos dados do usuário.

#### Scenario: Tarefa é concluída

- **WHEN** uma tarefa passa para `completed`
- **THEN** os contadores, a porcentagem geral e o progresso da disciplina refletem a alteração após atualização dos dados

### Requirement: Próxima melhor ação possui prioridade determinística

Quando existir tarefa não concluída, o sistema DEVE sugerir uma única próxima ação. A ordem de prioridade é: atrasada, vence hoje, vence em até três dias, menor progresso da disciplina, prazo mais próximo e título em ordem alfabética.

#### Scenario: Há tarefa atrasada e outra futura

- **WHEN** existem tarefas pendentes, incluindo uma atrasada
- **THEN** a recomendação aponta a tarefa atrasada e a identifica como urgente

#### Scenario: Não há tarefa pendente

- **WHEN** todas as tarefas estão concluídas ou não há tarefas
- **THEN** o dashboard mostra um estado vazio de agenda tranquila, sem inventar uma recomendação

### Requirement: Onboarding reduz a primeira ação ao essencial

O dashboard DEVE orientar novos usuários primeiro a criar uma disciplina e depois uma tarefa, sem esconder a navegação principal.

#### Scenario: Conta sem disciplinas

- **WHEN** um usuário autenticado ainda não possui disciplina
- **THEN** o painel de primeiros passos oferece a criação da primeira disciplina

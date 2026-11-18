# Capacidade: dashboard Campus

## Purpose

Dar uma visão imediata da jornada acadêmica por meio de um Campus de aprendizagem, tornando visível o avanço por disciplina e a próxima ação mais útil.

## Requirements

### Requirement: Campus é a experiência principal do dashboard

O dashboard SHALL usar a direção visual de Campus de aprendizagem, e não o protótipo antigo de ilhas. Disciplinas SHALL ser apresentadas como áreas/prédios em evolução, com cor e percentual de progresso.

#### Scenario: Usuário abre o dashboard com disciplinas

- **WHEN** o dashboard é carregado para um usuário com disciplinas
- **THEN** o Campus mostra o progresso individual e geral de forma compreensível

### Requirement: Indicadores refletem tarefas reais

O dashboard SHALL apresentar total de disciplinas, progresso geral, entregas nos próximos três dias e tarefas em atraso, calculados somente a partir dos dados do usuário.

#### Scenario: Tarefa é concluída

- **WHEN** uma tarefa passa para `completed`
- **THEN** os contadores, a porcentagem geral e o progresso da disciplina refletem a alteração após atualização dos dados

### Requirement: Próxima melhor ação possui prioridade determinística

O sistema SHALL sugerir uma próxima ação entre tarefas pendentes, ordenando por: urgência (atrasada, hoje, até três dias, futura), caber no tempo disponível, menor excesso de duração, menor dificuldade quando há menos de 30 minutos disponíveis, menor progresso da disciplina, prazo e título em ordem alfabética. Sem estimativas, considera 30 minutos e dificuldade 3.

#### Scenario: Há tarefa atrasada e outra futura

- **WHEN** existem tarefas pendentes, incluindo uma atrasada
- **THEN** a recomendação aponta a tarefa atrasada e a identifica como urgente

#### Scenario: Não há tarefa pendente

- **WHEN** todas as tarefas estão concluídas ou não há tarefas
- **THEN** o dashboard mostra um estado vazio de agenda tranquila, sem inventar uma recomendação

### Requirement: Missões de revisão acompanham a tarefa sem perder histórico

Uma tarefa concluída SHALL possuir no máximo uma missão de revisão, programada três dias após a data de conclusão no calendário de São Paulo. A sincronização SHALL manter a disciplina da missão coerente com a tarefa na mesma transação, preservando o conteúdo de missões existentes.

#### Scenario: Transferência de tarefa concluída entre disciplinas do usuário

- **WHEN** o usuário transfere uma tarefa concluída para outra disciplina própria
- **THEN** a missão existente SHALL acompanhar a nova disciplina sem duplicação
- **AND** SHALL preservar agendamento, estado, perguntas, respostas, avaliação e data de conclusão existentes
- **AND** chamadas repetidas de sincronização SHALL manter o mesmo resultado, inclusive antes do commit

#### Scenario: Revisão ainda não iniciada ou em andamento

- **WHEN** a tarefa muda de disciplina antes ou durante a revisão
- **THEN** a mudança SHALL NOT gerar perguntas automaticamente nem reiniciar o progresso
- **AND** perguntas existentes que mencionem a disciplina antiga SHALL permanecer como conteúdo histórico
- **AND** uma revisão sem perguntas SHALL usar a disciplina atual somente quando o aluno iniciar a revisão

#### Scenario: Exclusão após transferência

- **WHEN** a disciplina antiga é excluída após a transferência confirmada
- **THEN** a tarefa transferida e sua missão SHALL permanecer intactas
- **AND** excluir a tarefa ou sua disciplina atual SHALL manter a exclusão em cascata existente

#### Scenario: Isolamento entre usuários

- **WHEN** um usuário tenta transferir uma tarefa para disciplina de outro usuário ou acessar sua revisão
- **THEN** a operação SHALL ser recusada
- **AND** vínculos inconsistentes entre tarefa e disciplina da missão SHALL NOT expor dados pela listagem ou consulta de revisões

#### Scenario: Tarefa reaberta

- **WHEN** uma tarefa deixa o estado concluído
- **THEN** uma revisão pendente ou em andamento SHALL ser removida conforme o ciclo existente
- **AND** uma revisão já concluída SHALL ser preservada, acompanhando a disciplina atual da tarefa

### Requirement: Onboarding reduz a primeira ação ao essencial

O dashboard SHALL orientar novos usuários primeiro a criar uma disciplina e depois uma tarefa, sem esconder a navegação principal.

#### Scenario: Conta sem disciplinas

- **WHEN** um usuário autenticado ainda não possui disciplina
- **THEN** o painel de primeiros passos oferece a criação da primeira disciplina

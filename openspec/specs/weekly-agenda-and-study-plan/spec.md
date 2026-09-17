# Capacidade: agenda semanal e plano de estudo

## Propósito

Transformar prazos em uma rota semanal de missões e oferecer contexto humano sobre o ritmo de conclusão.

## Requisitos

### Requirement: Agenda semanal navegável

A rota `#agenda` DEVE mostrar sete dias, de segunda a domingo, e permitir navegar para semana anterior, atual e próxima. Uma tarefa deve aparecer no dia de seu prazo.

#### Scenario: Usuário percorre semanas

- **WHEN** o usuário seleciona semana anterior ou próxima
- **THEN** a agenda mostra exatamente o intervalo de sete dias correspondente e preserva a navegação da aplicação

#### Scenario: Tarefa vence na semana exibida

- **WHEN** uma tarefa possui prazo dentro da semana aberta
- **THEN** ela aparece no dia correto com título, disciplina e status

### Requirement: A agenda atualiza o progresso

O seletor de status da agenda DEVE usar a mesma atualização de tarefa das demais telas e propagar a alteração para o dashboard, lista de tarefas e agenda.

#### Scenario: Conclusão dentro da agenda

- **WHEN** o usuário marca uma tarefa como concluída na agenda
- **THEN** a tarefa permanece coerente na tela e os dados dependentes são atualizados

### Requirement: Resumo semanal humano

Acima da rota, a agenda DEVE informar quantas tarefas foram concluídas no período, no formato “Você concluiu X de Y tarefas esta semana”, e mostrar uma mensagem adaptativa de incentivo, atenção ou organização.

#### Scenario: Semana sem tarefas

- **WHEN** não há tarefas no intervalo semanal
- **THEN** o resumo incentiva planejamento sem informar porcentagens ou pendências inexistentes

### Requirement: Missão principal e conexão com o Campus

O dia selecionado DEVE destacar uma missão principal; se não existir tarefa no dia, deve apresentar uma sugestão de reorganização. A agenda DEVE exibir o progresso das disciplinas com entregas na semana e link de retorno ao Campus.

#### Scenario: Dia sem prazo

- **WHEN** o usuário seleciona um dia sem tarefas
- **THEN** a agenda mostra “Dia livre para reorganizar” e oferece criar uma tarefa, sem classificar o dia como erro

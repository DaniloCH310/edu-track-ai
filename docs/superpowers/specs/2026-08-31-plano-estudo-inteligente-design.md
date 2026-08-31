# Plano de estudo inteligente — design

## Objetivo

Exibir no dashboard uma única próxima ação de estudo, escolhida de forma determinística e acompanhada de uma explicação clara.

## Regra de prioridade

Entre tarefas não concluídas, a ordem é: atrasadas; vencem hoje; vencem nos próximos três dias; tarefas de disciplinas com menor progresso; e, por fim, o prazo mais próximo. Empates usam título em ordem alfabética.

## Contrato

`GET /api/dashboard` passa a devolver `recommended_task`, ou `null` quando não houver tarefa pendente. A recomendação inclui tarefa, disciplina, prazo, nível (`urgent`, `attention` ou `routine`) e texto explicativo.

## Interface

O dashboard mostra um cartão “Plano de estudo inteligente” com a tarefa sugerida, disciplina, prazo, motivo e atalho para a Agenda. Estados sem tarefas orientam o estudante a criar a primeira tarefa.

## Critérios de aceite

1. Uma tarefa atrasada é recomendada antes de qualquer tarefa futura.
2. Entre tarefas futuras semelhantes, a disciplina com menor progresso é priorizada.
3. O motivo da recomendação corresponde à regra aplicada.
4. Sem tarefas pendentes, a API retorna `null` e a interface mostra estado vazio.

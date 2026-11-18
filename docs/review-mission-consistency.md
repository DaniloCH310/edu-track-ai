# Consistência das missões de revisão — P7

## Ciclo e transação

`TaskRepository.create`, `update` e `update_status` chamam
`ReviewMissionRepository.sync_for_task` antes do commit. Ao concluir uma tarefa,
a missão é agendada para três dias depois, no calendário de São Paulo.
`is_available` libera revisões cuja data chegou, exceto as concluídas.
`create_questions` gera perguntas apenas se a lista estiver vazia; `assess_answers`
salva respostas, avaliação e data de conclusão.

A sincronização atualiza `subject_id` de uma missão existente sem reiniciar seu
estado. Antes da consulta, um flush explícito permite enxergar uma missão criada anteriormente
na mesma transação. Não há commit próprio: falhas permitem desfazer tarefa e
missão juntas. A restrição única de `task_id` continua impedindo duas missões
persistidas para a mesma tarefa.

## Histórico e conteúdo

Transferir uma tarefa preserva o ID da missão, agendamento, perguntas, respostas,
avaliação e conclusão. Não há geração automática de perguntas por essa mudança.
Referências à disciplina antiga são preservadas literalmente como parte do
conteúdo estudado. Não fazemos substituição textual, pois ela poderia mudar o
sentido das perguntas e invalidar respostas e avaliações já registradas.

Se a missão ainda não tem perguntas, seu início usa a disciplina atual. Se já
tem perguntas, elas são reutilizadas. A avaliação solicitada posteriormente
continua recebendo as perguntas preservadas e o contexto atual da tarefa e da
disciplina; não existe snapshot separado da disciplina antiga. Uma avaliação já
concluída não é recalculada pela transferência.

Reabrir uma tarefa mantém a regra anterior: remove revisões pendentes/em andamento
e preserva revisões concluídas. Mesmo essa revisão concluída acompanha uma eventual
troca de disciplina. Portanto, reabrir é diferente de apenas transferir.

## Exclusão e privacidade

As FKs de `ReviewMission.task_id`, `ReviewMission.subject_id` e
`AcademicTask.subject_id` mantêm `ON DELETE CASCADE`. Depois da transferência,
excluir a disciplina antiga não apaga a missão. Excluir a tarefa ou sua disciplina
atual continua apagando a missão; a P7 não altera essa política de negócio.

A API verifica a propriedade da tarefa e da disciplina de destino. Consultas de
revisão exigem que tarefa e missão pertençam à mesma disciplina do usuário.
Vínculos legados inconsistentes ficam indisponíveis nessas consultas, sem excluir
seu conteúdo, até uma sincronização da tarefa corrigir o vínculo.

Não há migração nem reparação em massa dos dados existentes. Nenhum dado real foi
alterado nesta correção. Registros inconsistentes anteriores precisam de revisão
separada antes de excluir suas disciplinas antigas. As FKs atuais não impõem a
igualdade entre as duas colunas `subject_id`: escritas diretas fora do repositório
ainda podem produzir inconsistências.

## Validação

`tests/unit/test_review_mission_sync.py` usa SQLite criado exclusivamente em memória,
com chaves estrangeiras habilitadas, e simulação da autorização da API. Testa
transferências nos três estados, preservação, idempotência, cascatas, isolamento e
rollback. Não usa `DATABASE_URL`, PostgreSQL ou serviços externos. Essa verificação
não substitui testes de migrações e concorrência em PostgreSQL dedicado e descartável.

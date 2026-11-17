# Tarefa 14 — Busca acadêmica de disciplinas

Implementação: FastAPI + Python/SQLAlchemy + PostgreSQL, preservando a arquitetura.
O enunciado pede disciplinas por nome ou por tarefas atrasadas. Cada filtro pode
ser usado sozinho; quando ambos são informados, a combinação é AND (interseção).
Não há ranking por relevância nem dependência de IA para esta consulta.

## Contrato

`GET /api/subjects` exige a sessão habitual do EduTrack.

| Parâmetro | Tipo | Comportamento |
|---|---|---|
| `query` | string opcional, máximo 160 caracteres | Parte literal do nome, ignorando maiúsculas/minúsculas; espaços nas extremidades removidos; vazio ignora o filtro |
| `overdue` | boolean opcional, padrão `false` | `true`: existe tarefa não concluída com prazo anterior a hoje em `America/Sao_Paulo`; `false`/omitido não filtra atraso |

`%` e `_` não funcionam como curingas. Não se promete equivalência entre letras
acentuadas e não acentuadas. O PostgreSQL aplica a comparação conforme sua collation.
O formato da resposta, ordenação por nome e isolamento pelo usuário são preservados.
Tarefas de hoje, futuras ou concluídas não qualificam uma disciplina como atrasada.
EXISTS evita duplicações quando há várias tarefas atrasadas. Não há alteração de dados.

## Demonstração no Swagger

Este roteiro descreve uma demonstração a realizar, não uma captura já executada.
Use uma conta e dados demonstrativos; não execute a suíte de testes sobre o banco
da apresentação. A proteção P1 continua obrigatória para testes PostgreSQL.

1. Abra `http://127.0.0.1:8000/docs` no mesmo host usado para acessar o EduTrack.
2. Execute `POST /api/auth/login` com sua conta demonstrativa (ou entre pela tela).
   O navegador recebe o cookie HttpOnly e o envia nas próximas requisições.
   Não copie cookies, senhas ou tokens para screenshots.
3. Com os CRUDs existentes, prepare disciplinas: Python Básico, Python Avançado,
   História e Sem tarefas. Em Python Básico, registre uma tarefa pendente ontem;
   em Python Avançado, duas atrasadas, uma pendente e outra em andamento; em
   História, uma concluída ontem e outra pendente hoje. Use a data de São Paulo.
4. Abra `GET /api/subjects`, clique em **Try it out** e execute os exemplos abaixo.
5. Mostre a URL, o status 200 e a lista retornada. Para comprovar o isolamento,
   repita com outra conta com disciplinas distintas, encerrando antes a sessão.

| Requisição | Resultado esperado para o cenário acima |
|---|---|
| `/api/subjects` | Todas as quatro disciplinas da conta |
| `/api/subjects?query=pYtHoN` | Python Básico e Python Avançado |
| `/api/subjects?query=inexistente` | `[]` |
| `/api/subjects?overdue=true` | Python Básico e Python Avançado, uma vez cada |
| `/api/subjects?query=Básico&overdue=true` | Somente Python Básico |
| `/api/subjects?query=História&overdue=true` | `[]` |
| `/api/subjects?query=%20%20&overdue=false` | Mesma lista sem filtros |

Exemplo ilustrativo de resposta (IDs e datas fictícios, não resultado de execução):

```json
[
  {
    "id": "11111111-1111-4111-8111-111111111111",
    "name": "Python Básico",
    "professor": null,
    "workload_hours": 30,
    "description": null,
    "period": null,
    "color": "#6750A4",
    "start_date": null,
    "end_date": null,
    "progress": 0,
    "source": "local",
    "created_at": "2026-11-17T12:00:00Z",
    "updated_at": "2026-11-17T12:00:00Z"
  }
]
```

O campo `progress` mantém o contrato existente; a busca não introduz novo cálculo.
Entrada inválida (query acima do limite ou boolean inválido) retorna 422.
Sem sessão válida, retorna 401. Não há parâmetro que permita escolher outro usuário.

## Evidência e limites da validação

- `app/api/subjects.py`: contrato HTTP e documentação Swagger.
- `app/repositories/subjects.py`: filtro parametrizado e EXISTS correlacionado.
- `tests/unit/test_subject_search.py`: 15 testes locais aprovados com HTTP real
  via TestClient e banco SQLite exclusivamente em memória; guard impede uso
  acidental do engine PostgreSQL. Inclui compilação SQL no dialeto PostgreSQL,
  fronteira de data UTC/São Paulo, autenticação e consulta com caracteres especiais.
- Ruff e OpenSpec devem ser verificados na versão entregue.
- Não houve execução PostgreSQL real nem demonstração manual no Swagger nesta etapa.
  Compilação do dialeto não substitui execução no PostgreSQL descartável do CI.
- Não há novas dependências, migrações, mudanças de frontend ou serviços externos.

Para a entrega acadêmica, selecionar uma captura da busca por nome e outra do
filtro de atraso/combinado e fornecer o link do futuro PR. Não há PR novo nesta
etapa: a alteração é commitada localmente, sem push ou merge. A equivalência ao
Xano é o endpoint FastAPI chamando o repositório Python e consultando PostgreSQL.

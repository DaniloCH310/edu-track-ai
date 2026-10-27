# EduTrack — roteiro da Avaliação Parcial 02

Preparado em 01/10/2026 a partir dos arquivos atuais do projeto e da captura da atividade **“Avaliação Parcial 02 - Aplicação”**, do professor Evandro Victor Rocha Deliberal. Na captura: valor de 10 pontos e entrega em 6 de outubro.

Atividade: https://classroom.google.com/u/1/c/ODcxMjM5MzQ4NTUz/a/ODcxMjQyOTk5ODIw/details

O conteúdo da atividade foi conferido pela captura fornecida; a página autenticada do Classroom não pôde ser confirmada nesta consulta.

## O que será avaliado

| Exigência da captura | Evidência a apresentar |
|---|---|
| Todas as telas da aplicação | Autenticação, disciplinas, tarefas, agenda, EDU IA, integrações e formulários/estados complementares |
| Dicionário de dados | Entidades, campos, tipos, obrigatoriedade, PK, FK, relacionamentos e validações |
| APIs do modelo de dados | Swagger/OpenAPI, rotas de disciplinas e tarefas, JSON de entrada e saída |
| CRUD funcionando | Criar, consultar, editar e excluir registros pela interface; confirmar pela API |

**Observação expressa do professor:** dashboard, insights e documentação `.md` ficam para a apresentação final. Por isso, o Campus só aparece brevemente na transição após o login; a exposição desta parcial concentra-se nos quatro itens acima. Os resumos analíticos da agenda também não precisam ser aprofundados. Este arquivo é seu guia de ensaio, não um bloco de documentação a apresentar.

Tempo sugerido: **12–15 minutos**, adaptável ao tempo concedido pelo professor.

## Preparação antes da apresentação

1. Inicie pelo arquivo `Iniciar EduTrack.cmd`, na raiz. Abra `http://127.0.0.1:8000`.
2. Confira `/api/version` e se a interface é a atual. A aplicação atual é `app/main.py`; **`app.py` na raiz é o protótipo Streamlit legado**.
3. Use uma conta de demonstração. Se quiser mostrar dados reais já cadastrados, evite projetar informações pessoais desnecessárias.
4. Deixe três abas prontas: aplicação, `http://127.0.0.1:8000/docs` e `http://127.0.0.1:8000/openapi.json`. Use sempre o mesmo endereço e porta: `localhost` e `127.0.0.1` não compartilham o mesmo cookie.
5. Entre na aplicação antes de usar o Swagger. A autenticação usa o cookie HttpOnly `edutrack_session`; não depende de colar um token Bearer no botão Authorize.
6. Ensaie criação, edição, conclusão e exclusão com dados descartáveis. O roteiro abaixo descreve o comportamento implementado; esta preparação não executou um teste ao vivo do CRUD.
7. Confira previamente o EDU IA e a conexão Classroom. Se houver indisponibilidade do provedor ou bloqueio institucional, mostre o estado real e prossiga com o CRUD local.
8. Para a tela de redefinição de senha, prepare previamente o fluxo com a conta de teste e um link válido recebido por e-mail. Não projete o token. Uma captura do ensaio pode servir de apoio, identificada como captura, se o e-mail atrasar.
9. Deixe os arquivos da lista abaixo abertos no editor. Não abra `.env`, credenciais ou registros com segredos.

## Arquivos para deixar abertos, nesta ordem

Todos os caminhos são relativos à raiz do projeto.

| Ordem | Arquivo | O que apontar |
|---|---|---|
| 1 | [app/main.py](../app/main.py) | `create_app()`, registro das rotas e serviço dos arquivos estáticos |
| 2 | [app/static/index.html](../app/static/index.html) | Estrutura das telas, navegação, formulários e diálogos |
| 3 | [app/models/user.py](../app/models/user.py) | `User`: usuário e propriedade das disciplinas |
| 4 | [app/models/subject.py](../app/models/subject.py) | `Subject`: tabela, campos e FK `user_id` |
| 5 | [app/models/task.py](../app/models/task.py) | `AcademicTask`, `TaskStatus` e FK `subject_id` |
| 6 | [app/schemas/subject.py](../app/schemas/subject.py) | Contratos de entrada/saída e validações de disciplina |
| 7 | [app/schemas/task.py](../app/schemas/task.py) | Contratos de tarefa, dificuldade e tempo estimado |
| 8 | [app/api/subjects.py](../app/api/subjects.py) | Rotas GET, POST, PUT e DELETE |
| 9 | [app/api/tasks.py](../app/api/tasks.py) | CRUD de tarefas e PATCH de status |
| 10 | [app/repositories/subjects.py](../app/repositories/subjects.py) | Consultas por usuário e operações `commit()` |
| 11 | [app/repositories/tasks.py](../app/repositories/tasks.py) | Persistência, filtros, conclusão e agendamento de revisão |
| 12 | [tests/api/test_subjects.py](../tests/api/test_subjects.py) e [tests/api/test_tasks.py](../tests/api/test_tasks.py) | Testes existentes de CRUD e isolamento entre usuários |

Não leia os arquivos inteiros na apresentação: aponte a classe ou função indicada e volte para a demonstração.

## Roteiro de fala e demonstração

### 1. Abertura — 40 segundos

**Fala sugerida:**

> “O EduTrack organiza a rotina acadêmica em um só lugar: o aluno cadastra suas disciplinas, acompanha tarefas e prazos e pode tirar dúvidas com o EDU IA. Nesta avaliação vou demonstrar as telas, o modelo de dados, as APIs e o CRUD funcionando. A análise detalhada do dashboard e dos insights fica para a apresentação final, conforme a orientação da atividade.”

**Mostre:** página inicial. Abra rapidamente `app/main.py`.

> “O front-end usa HTML, CSS e JavaScript. O back-end é Python com FastAPI, e os dados são persistidos em PostgreSQL por meio do SQLAlchemy.”

### 2. Autenticação — 1 minuto

**Mostre:** Entrar → Criar conta → Esqueci minha senha → tela de redefinição preparada → login na conta de demonstração.

> “O acesso identifica o aluno para que cada um visualize e altere apenas seus registros. Há cadastro, login e recuperação de senha. O botão de olho permite conferir o que foi digitado.”

Use somente uma senha de demonstração se for mostrar o botão de visualização. Após entrar, navegue para Disciplinas; não gaste o tempo desta parcial explicando o Campus.

**Arquivos de apoio:** `app/static/index.html`, `app/static/js/auth.js`, `app/api/auth.py`, `app/api/dependencies.py`.

**Se perguntarem sobre segurança:** o modelo armazena `password_hash`; as rotas autenticadas utilizam `CurrentUser`, e os repositórios filtram a propriedade dos dados.

### 3. Disciplinas: criar, consultar e editar — 2 minutos

**Ação 1 — Create:** clique em **“+ Inaugurar disciplina”** e cadastre:

| Campo | Valor de demonstração |
|---|---|
| Nome | Python Aplicado — Demonstração |
| Professor | Professor de demonstração |
| Carga horária | 80 |
| Período | 2026.2 |
| Descrição | Disciplina temporária para apresentar o CRUD |

> “Cada disciplina é um registro com identificação, carga horária e informações acadêmicas. Ao salvar, o navegador envia os dados à API e recebe o registro criado.”

**Ação 2 — Read:** abra a disciplina, mostre seus detalhes e a visualização em lista. Recarregue a página e confirme que o cadastro permanece.

**Ação 3 — Update:** edite a carga horária de 80 para 100 e acrescente “Exercícios de funções e listas” à descrição. Salve e mostre a alteração.

**Arquivos:** `app/static/js/subjects.js` (`openSubjectForm`, `submitSubject`), `app/api/subjects.py` (`create_subject`, `get_subject`, `update_subject`) e `app/repositories/subjects.py`.

**Importante para a sequência:** ainda não exclua a disciplina; ela será usada pela tarefa.

### 4. Tarefas: criar, consultar e editar — 2 minutos

**Ação 1:** em Tarefas, clique em **“+ Nova missão”**. Crie:

| Campo | Valor de demonstração |
|---|---|
| Título | Praticar funções em Python — Demonstração |
| Disciplina | Python Aplicado — Demonstração |
| Prazo | 06/10/2026, se a apresentação ocorrer nessa semana |
| Dificuldade | Moderada, equivalente a 3 |
| Tempo estimado | 25 minutos |
| Status | Pendente |
| Descrição | Criar uma função que receba três notas e retorne a média |

Se a apresentação ocorrer em outra semana, adapte o prazo para um dia visível na agenda.

> “A tarefa pertence a uma disciplina. Além do prazo e status, o aluno informa dificuldade e tempo estimado.”

**Ação 2:** busque “funções”, filtre pela disciplina e alterne entre quadro e lista.

**Ação 3:** edite a descrição; depois altere o status para **Em andamento**. Mostre a atualização. Deixe a tarefa criada para usá-la na agenda e no Swagger.

**Arquivos:** `app/static/js/tasks.js` (`openTaskForm`, `submitTask`, `changeStatus`), `app/api/tasks.py` e `app/repositories/tasks.py`.

### 5. Demais telas — 1 minuto e 30 segundos

| Tela | O que fazer | Fala sugerida | Arquivo |
|---|---|---|---|
| Agenda | Vá à semana do prazo, selecione o dia e localize a tarefa criada | “A agenda apresenta as mesmas tarefas organizadas por prazo; não exige cadastrar a atividade novamente.” | `app/static/js/agenda.js` |
| EDU IA | Mostre Nova conversa, histórico e campo de mensagem; se o serviço estiver disponível, pergunte “Como escrever uma função que calcula a média de três notas?” | “O tutor apoia a compreensão do conteúdo e mantém conversas vinculadas ao aluno.” | `app/static/js/edu-ia.js`, `app/api/edu_ia.py` |
| Integrações | Mostre o cartão Classroom e o estado atual da conexão | “A integração importa disciplinas e atividades em modo somente leitura. Sua disponibilidade também depende das permissões da conta Google.” | `app/static/js/integrations.js`, `app/api/classroom.py` |

Não prometa uma sincronização bem-sucedida se a conta institucional estiver bloqueada. A configuração local da integração não libera uma política da instituição.

**Telas/estados complementares:** os formulários de criação e edição já foram mostrados no CRUD. Mostre a confirmação de exclusão na etapa 8. Se a conta de teste ainda não tiver disciplinas, mostre o onboarding antes de cadastrar a primeira. Se houver uma missão de revisão disponível, apresente brevemente o painel de perguntas e respostas do EDU IA; a análise de domínio e os indicadores ficam para a final. Esse painel está no módulo `app/static/js/edu-ia.js` e suas rotas em `app/api/review_missions.py`.

### 6. Dicionário de dados — 2 minutos

**Abra:** `app/models/user.py`, `app/models/subject.py` e `app/models/task.py`.

> “O núcleo do modelo tem três entidades. Um usuário possui várias disciplinas; uma disciplina possui várias tarefas. As chaves estrangeiras representam esses vínculos e garantem a integridade dos dados.”

Apresente as tabelas do apêndice A como apoio. Destaque:

1. `id`: identificador UUID e chave primária.
2. `subjects.user_id`: chave estrangeira para o usuário.
3. `academic_tasks.subject_id`: chave estrangeira para a disciplina.
4. `due_date`, `status` e `completed_at`: prazo, situação e momento da conclusão.
5. `difficulty` e `estimated_minutes`: informações usadas na organização do estudo.

**Abra:** `app/schemas/task.py`.

> “Os modelos descrevem a persistência. Os schemas validam os dados que entram e saem pela API. Por exemplo, a dificuldade aceita valores de 1 a 5 e o tempo estimado de 5 a 480 minutos.”

Não apresente essas faixas como restrições CHECK do PostgreSQL: no código conferido, elas são validações Pydantic. Em disciplinas, carga positiva e intervalo de datas também têm restrições no modelo do banco.

**Se perguntarem como o banco é criado:** mostre `alembic/versions/20260827_0001_initial_schema.py`. Os novos campos de personalização estão em `alembic/versions/20260922_0005_personalized_next_action.py`; as demais migrações acrescentam Classroom, EDU IA e revisões.

### 7. APIs do modelo de dados — 2 minutos

**Abra:** `http://127.0.0.1:8000/docs`, já autenticado no mesmo navegador/origem.

> “O Swagger apresenta os contratos da API gerados pelo FastAPI. A mesma API utilizada por esta página é chamada pela interface.”

1. Expanda **disciplinas** e execute `GET /api/subjects` com **Try it out → Execute**. Localize a disciplina de demonstração e seu `id`.
2. Expanda **tarefas** e execute `GET /api/tasks`, filtrando pelo `subject_id` copiado. Mostre título, disciplina, prazo e status no JSON.
3. Copie o `id` da tarefa. Execute `PATCH /api/tasks/{task_id}/status` com `{"status":"completed"}`.
4. Volte à aplicação, atualize a página e confirme que a tarefa está concluída. Isso mostra uma alteração feita pela API aparecendo na interface.
5. No Swagger, aponte também POST, PUT e DELETE. As operações completas de criação, consulta, edição e exclusão serão comprovadas pelo fluxo inteiro da apresentação; não é necessário duplicar cada cadastro.

> “GET consulta, POST cria, PUT atualiza o formulário completo e DELETE remove. O PATCH permite alterar somente o status. Cada acesso passa pela identificação do usuário e pela conferência da propriedade do registro.”

**Arquivos:** `app/api/subjects.py`, `app/api/tasks.py`, `app/schemas/subject.py`, `app/schemas/task.py`.

**Validação opcional, se sobrar tempo:** envie um POST de tarefa com os mesmos campos válidos e `difficulty: 6`; o contrato prevê rejeição HTTP 422. Não espere erro de validação ao simplesmente colar um UUID fictício: isso pode produzir erro de formato ou disciplina não encontrada.

Se o Swagger retornar 401, confira o login e a origem usados. Não exponha cookies ou credenciais para tentar explicar o problema durante a apresentação.

### 8. Excluir e comprovar o CRUD completo — 1 minuto

1. Na interface, exclua **somente a tarefa de demonstração**, mostrando o diálogo de confirmação.
2. Recarregue e confirme que ela não aparece mais; opcionalmente, repita a consulta no Swagger.
3. Exclua **somente a disciplina de demonstração** e confirme sua remoção da lista.

> “Com isso, demonstrei as quatro operações: criar, consultar, atualizar e excluir, com as informações persistidas e refletidas na aplicação.”

**Arquivos:** `delete_task` em `app/api/tasks.py`, `delete_subject` em `app/api/subjects.py` e os respectivos repositórios.

**Observação para explicar, sem apagar dados reais:** excluir uma disciplina também remove suas tarefas. As relações usam `ON DELETE CASCADE`; o formulário informa essa consequência. Como a tarefa de demonstração já foi excluída, não haverá outras atividades de teste dependentes neste fluxo.

### 9. Encerramento — 30 segundos

> “O EduTrack demonstrou as telas operacionais, o modelo de dados e suas validações, as APIs e o CRUD de disciplinas e tarefas. Para a apresentação final, vou aprofundar o Campus, os indicadores e a documentação do projeto.”

Se perguntarem sobre testes, abra `tests/api/test_subjects.py` e `tests/api/test_tasks.py`. Aponte `test_subject_crud_is_scoped_to_authenticated_user`, `test_task_crud_and_completion_timestamp` e os testes que impedem acesso a dados de outro usuário. A existência desses testes não substitui a demonstração ao vivo nem uma execução recente da suíte.

## Apêndice A — dicionário de dados para consulta

Fonte: arquivos atuais em `app/models/` e validações em `app/schemas/`. Descreve o código conferido, não uma inspeção do schema de um banco em execução.

PK = chave primária; FK = chave estrangeira; NULL = ausência permitida. Os defaults indicados nos modelos podem ser aplicados pelo ORM; não assuma que todos são defaults SQL.

### Núcleo acadêmico

| Tabela/campo | Tipo | NULL? | Regra/finalidade |
|---|---|---|---|
| users.id | UUID | Não | PK gerada pela aplicação |
| users.name | VARCHAR(120) | Não | Nome do aluno |
| users.email | VARCHAR(320) | Não | Único e indexado |
| users.password_hash | VARCHAR(255) | Não | Hash da senha |
| users.is_active | BOOLEAN | Não | Padrão True no modelo |
| subjects.id | UUID | Não | PK |
| subjects.user_id | UUID | Não | FK users.id; exclusão em cascata |
| subjects.name | VARCHAR(160) | Não | Nome da disciplina; 1–160 caracteres na API |
| subjects.professor | VARCHAR(160) | Sim | Professor |
| subjects.workload_hours | INTEGER | Não | Carga > 0 no banco; API limita a 10.000 |
| subjects.description | TEXT | Sim | Descrição; API limita a 4.000 caracteres |
| subjects.period | VARCHAR(40) | Sim | Período letivo |
| subjects.color | VARCHAR(7) | Não | Padrão #6750A4; API valida hexadecimal |
| subjects.start_date | DATE | Sim | Início |
| subjects.end_date | DATE | Sim | Fim; não anterior ao início quando ambos existem |
| academic_tasks.id | UUID | Não | PK |
| academic_tasks.subject_id | UUID | Não | FK subjects.id; exclusão em cascata |
| academic_tasks.title | VARCHAR(200) | Não | Título; 1–200 caracteres na API |
| academic_tasks.description | TEXT | Sim | API limita a 4.000 caracteres |
| academic_tasks.due_date | DATE | Não | Prazo; armazena data, não horário |
| academic_tasks.status | ENUM task_status | Não | pending, in_progress ou completed |
| academic_tasks.difficulty | INTEGER | Não | Padrão 3; API aceita 1–5 |
| academic_tasks.estimated_minutes | INTEGER | Não | Padrão 30; API aceita 5–480 |
| academic_tasks.completed_at | TIMESTAMP com fuso | Sim | Preenchido ao concluir; limpo ao reabrir |

As três tabelas acima herdam `created_at` e `updated_at`, ambos TIMESTAMP com fuso e obrigatórios, de `app/models/base.py`.

**Cardinalidades:** usuário 1:N disciplinas; disciplina 1:N tarefas. A tarefa pertence ao usuário por meio da disciplina, sem coluna `user_id` duplicada nela.

**Campos derivados de saída:** `subject_name`, `source`, `external_url` e o progresso exibido na interface não devem ser apresentados como colunas da tabela `academic_tasks`. Confira as propriedades dos modelos e os schemas de saída. A agenda reutiliza tarefas e prazos; não há tabela própria de agenda nesses modelos.

### Entidades complementares

Todas têm `id UUID` como PK. As tabelas de conversas, revisões e Classroom também herdam `created_at` e `updated_at` de `TimestampMixin`. Os campos abaixo são complementares ao núcleo e podem ser consultados se o professor perguntar.

| Tabela e arquivo | Campos e tipos | Relações/regras principais |
|---|---|---|
| password_reset_tokens — `app/models/user.py` | user_id UUID; token_hash VARCHAR(64); expires_at TIMESTAMP com fuso; used_at TIMESTAMP com fuso NULL; created_at TIMESTAMP com fuso | user_id FK users; token_hash único; campos restantes obrigatórios |
| edu_ai_conversations — `app/models/edu_ia.py` | user_id UUID; subject_id UUID NULL; task_id UUID NULL; title VARCHAR(200) | user_id FK users CASCADE; subject_id/task_id FKs SET NULL; título obrigatório |
| edu_ai_messages — `app/models/edu_ia.py` | conversation_id UUID; role ENUM(user, assistant); content TEXT; created_at TIMESTAMP com fuso | Todos obrigatórios; FK conversa CASCADE; conversa 1:N mensagens |
| review_missions — `app/models/review_mission.py` | task_id UUID; subject_id UUID; due_date DATE; status ENUM(pending, in_progress, completed); questions JSON; answers JSON; mastery_percent INTEGER NULL; mastery_summary TEXT NULL; completed_at TIMESTAMP com fuso NULL | task_id único, FK tarefa CASCADE; subject_id FK disciplina CASCADE; demais campos obrigatórios; listas padrão vazias |
| private.classroom_connections — `app/models/classroom.py` | user_id UUID; encrypted_refresh_token TEXT; granted_scopes TEXT; last_synced_at TIMESTAMP com fuso NULL; last_error_code VARCHAR(80) NULL | user_id único, FK users CASCADE; primeiros três campos obrigatórios |
| private.classroom_course_links — `app/models/classroom.py` | connection_id UUID; subject_id UUID; classroom_course_id VARCHAR(128); course_state VARCHAR(40) | Todos obrigatórios; FKs conexão/disciplina CASCADE; subject_id único; par conexão/curso externo único |
| private.classroom_task_links — `app/models/classroom.py` | course_link_id UUID; task_id UUID; classroom_coursework_id VARCHAR(128); classroom_submission_id VARCHAR(128) NULL; alternate_link TEXT; source_updated_at TIMESTAMP com fuso NULL | FKs vínculo do curso/tarefa CASCADE; task_id único; par vínculo/atividade externa único; demais campos obrigatórios |

Uma tarefa pode ter até uma missão de revisão pelo vínculo único `task_id`. Ao concluir uma tarefa, o repositório agenda a revisão para três dias depois, considerando o dia do aluno em America/Sao_Paulo. Mostre `app/repositories/review_missions.py` apenas se perguntarem sobre esse comportamento.

Não projete os valores de hashes, tokens de recuperação ou `encrypted_refresh_token`; basta mostrar suas definições no modelo.

## Apêndice B — APIs que demonstram o CRUD

| Recurso | Criar | Consultar | Atualizar | Excluir |
|---|---|---|---|---|
| Disciplina | POST /api/subjects | GET /api/subjects e GET /api/subjects/{subject_id} | PUT /api/subjects/{subject_id} | DELETE /api/subjects/{subject_id} |
| Tarefa | POST /api/tasks | GET /api/tasks e GET /api/tasks/{task_id} | PUT /api/tasks/{task_id}; PATCH /api/tasks/{task_id}/status | DELETE /api/tasks/{task_id} |

Respostas esperadas: POST 201; GET, PUT e PATCH 200; DELETE 204 sem corpo. Sem sessão: 401. Registro não encontrado ou de outro usuário: 404 nas consultas individuais protegidas. Payload inválido: 422.

POST de disciplina para um ensaio pelo Swagger:

```json
{
  "name": "Python Aplicado — Demonstração",
  "professor": "Professor de demonstração",
  "workload_hours": 80,
  "description": "Disciplina temporária para apresentar o CRUD",
  "period": "2026.2",
  "color": "#6750A4"
}
```

POST de tarefa — substitua o texto em `subject_id` pelo UUID real retornado no cadastro. Não execute o exemplo sem essa substituição:

```json
{
  "subject_id": "COLE_AQUI_O_UUID_REAL_DA_DISCIPLINA",
  "title": "Praticar funções em Python — Demonstração",
  "description": "Criar uma função que receba três notas e retorne a média",
  "due_date": "2026-10-06",
  "difficulty": 3,
  "estimated_minutes": 25,
  "status": "pending"
}
```

O PUT recebe os mesmos campos do formulário de criação: envie o formulário completo. Para mudar exclusivamente o status, use o PATCH mostrado no roteiro.

**Rotas complementares para apontar no Swagger:** `/api/auth/*`, `/api/edu-ia/conversations`, `/api/integrations/classroom` e `/api/reviews`. EDU IA possui criação, consulta e exclusão de conversas e envio de mensagens; não declare CRUD completo de conversas, pois não há rota de edição de conversa no módulo conferido. Integrações e revisões também têm operações específicas, não um CRUD genérico.

## Se o tempo cair para 8 minutos

- 30 s: problema e arquitetura.
- 1 min: autenticação e passagem pelas telas complementares.
- 3 min: criar disciplina, criar tarefa, consultar, editar e excluir os registros de teste.
- 1 min e 30 s: dicionário do núcleo e relacionamentos.
- 1 min e 30 s: Swagger, GET e explicação dos demais verbos.
- 30 s: encerramento.

Mantenha o foco em evidências visíveis. Uma operação feita com sucesso na tela e confirmada pela API vale mais do que uma longa leitura do código.

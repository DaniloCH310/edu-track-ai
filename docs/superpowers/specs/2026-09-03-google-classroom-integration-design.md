# Integração Google Classroom — Especificação de Design

## Objetivo

Permitir que cada estudante conecte sua própria conta Google, importe turmas e atividades com prazo do Google Classroom e sincronize o estado das entregas com o EduTrack. O primeiro lançamento é somente de leitura em relação ao Classroom: o EduTrack consulta dados, mas não cria, edita, entrega ou exclui recursos no Google.

## Escopo do MVP

O MVP inclui:

- conexão e desconexão individual por OAuth 2.0;
- importação de turmas ativas como disciplinas;
- importação de atividades publicadas e com prazo como tarefas;
- consulta da entrega do próprio estudante;
- sincronização manual idempotente;
- indicação visual da origem Google Classroom e link para a atividade original;
- resumo do último sincronismo, incluindo itens criados, atualizados e ignorados;
- tratamento explícito de bloqueio administrativo, autorização revogada e falhas transitórias.

O MVP não inclui:

- criação ou edição de atividades no Classroom;
- envio de trabalhos, anexos ou notas;
- leitura de colegas, professores ou listas de alunos;
- sincronização automática agendada ou por push notification;
- importação de atividades sem prazo;
- transformação do login principal do EduTrack em login social.

A sincronização periódica poderá ser adicionada depois sobre o mesmo serviço idempotente, sem alterar os vínculos persistidos neste MVP.

## Experiência do usuário

Uma nova rota `#integrations` será adicionada à navegação como **Integrações**. A tela terá um cartão Google Classroom com quatro estados:

1. **Não conectado:** explica quais dados serão lidos e oferece “Conectar Google Classroom”.
2. **Conectando:** desabilita ações duplicadas enquanto o navegador segue para o consentimento Google.
3. **Conectado:** mostra o último sincronismo e oferece “Sincronizar agora” e “Desconectar”.
4. **Ação necessária:** informa que a autorização expirou, foi revogada ou depende do administrador da instituição e oferece reconexão.

Após o callback OAuth, o usuário retorna para `/?classroom=connected#integrations`. Depois de um sincronismo, a tela apresenta contagens literais: turmas criadas/atualizadas, tarefas criadas/atualizadas e atividades sem prazo ignoradas.

Disciplinas e tarefas vinculadas recebem um selo **Google Classroom**. A tarefa inclui “Abrir no Classroom”, usando exclusivamente o `alternateLink` devolvido pela API. Os formulários locais continuam disponíveis, mas a sincronização volta a aplicar os campos canônicos descritos abaixo.

## Autorização Google

O backend FastAPI será um cliente OAuth confidencial e usará Authorization Code com PKCE. A autorização solicitará somente:

- `https://www.googleapis.com/auth/classroom.courses.readonly`;
- `https://www.googleapis.com/auth/classroom.coursework.me.readonly`.

O pedido usará `access_type=offline`, `include_granted_scopes=true` e `prompt=consent` quando for necessário obter ou renovar o refresh token. O callback validará:

- a sessão EduTrack atual;
- um `state` assinado, de uso único e com expiração de dez minutos;
- o `code_verifier` correspondente ao desafio PKCE;
- a presença dos escopos mínimos concedidos.

O `state` e o `code_verifier` serão guardados em cookie temporário `HttpOnly`, `SameSite=Lax`, com `Secure` em produção. O callback nunca enviará tokens ao frontend ou à URL.

O access token existirá somente em memória durante cada chamada. Apenas o refresh token será persistido, cifrado com Fernet por uma chave exclusiva `GOOGLE_TOKEN_ENCRYPTION_KEY`. Essa chave não será derivada de `JWT_SECRET`, não entrará no Git e será obrigatória quando as credenciais Google estiverem habilitadas.

## Configuração

As seguintes variáveis serão adicionadas a `.env.example`:

```dotenv
GOOGLE_CLASSROOM_ENABLED=false
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_OAUTH_REDIRECT_URI=http://127.0.0.1:8000/api/integrations/classroom/callback
GOOGLE_TOKEN_ENCRYPTION_KEY=
```

Em produção, `GOOGLE_OAUTH_REDIRECT_URI` deve usar HTTPS e coincidir literalmente com uma URI autorizada no Google Cloud Console. Quando `GOOGLE_CLASSROOM_ENABLED=false`, a aplicação inicia normalmente e a API informa que a integração está indisponível; isso preserva desenvolvimento local e ambientes sem credenciais.

## Persistência

Dados de integração ficarão no schema PostgreSQL `private`, que não é exposto pela Data API do Supabase. As tabelas também terão RLS habilitado como defesa adicional, sem políticas para `anon` ou `authenticated`; somente a conexão privada do backend terá acesso.

### `private.classroom_connections`

- `id UUID` — chave primária;
- `user_id UUID` — FK única para `users.id`, com exclusão em cascata;
- `encrypted_refresh_token TEXT` — token cifrado;
- `granted_scopes TEXT` — escopos normalizados e separados por espaço;
- `last_synced_at TIMESTAMPTZ NULL`;
- `last_error_code VARCHAR(80) NULL` — código sanitizado, nunca resposta completa do Google;
- `created_at` e `updated_at TIMESTAMPTZ`.

### `private.classroom_course_links`

- `id UUID` — chave primária;
- `connection_id UUID` — FK para a conexão, com exclusão em cascata;
- `subject_id UUID` — FK única para `subjects.id`, com exclusão em cascata;
- `classroom_course_id VARCHAR(128)`;
- `course_state VARCHAR(40)`;
- restrição única em `(connection_id, classroom_course_id)`;
- `created_at` e `updated_at TIMESTAMPTZ`.

### `private.classroom_task_links`

- `id UUID` — chave primária;
- `course_link_id UUID` — FK para o vínculo da turma, com exclusão em cascata;
- `task_id UUID` — FK única para `academic_tasks.id`, com exclusão em cascata;
- `classroom_coursework_id VARCHAR(128)`;
- `classroom_submission_id VARCHAR(128) NULL`;
- `alternate_link TEXT`;
- `source_updated_at TIMESTAMPTZ NULL`;
- restrição única em `(course_link_id, classroom_coursework_id)`;
- `created_at` e `updated_at TIMESTAMPTZ`.

Os vínculos, e não nomes ou títulos, serão usados para deduplicação. Um sincronismo repetido não criará novas disciplinas ou tarefas.

## Regras de importação

### Turmas

- Consultar apenas cursos com estado `ACTIVE` visíveis ao usuário autenticado.
- Criar uma disciplina quando não existir vínculo para o `classroom_course_id`.
- Preencher `name` com o nome da turma, `description` com a descrição disponível, `period` com a seção/período disponível e `workload_hours=1`, pois o Classroom não fornece carga horária.
- Em sincronismos posteriores, atualizar o nome e a descrição a partir do Classroom; preservar professor, cor, carga horária, período editado e datas locais.

### Atividades

- Consultar atividades publicadas de cada turma vinculada.
- Importar apenas itens com `dueDate` válido.
- Criar uma tarefa quando não existir vínculo para `(course_link_id, classroom_coursework_id)`.
- Atualizar título, descrição, prazo e `alternateLink` em sincronismos posteriores.
- Não apagar tarefas quando uma atividade desaparecer, uma turma for arquivada ou o acesso for perdido. O resultado do sincronismo registra a ocorrência, evitando perda silenciosa de dados locais.

### Estado da entrega

- `TURNED_IN` e `RETURNED` definem a tarefa local como `completed` e preenchem `completed_at` quando ainda estiver vazio.
- `RECLAIMED` reabre a tarefa como `pending` e limpa `completed_at`.
- `NEW` e `CREATED` mantêm `in_progress` quando o estudante já iniciou a missão no EduTrack; nos demais casos usam `pending`.
- Ausência de `StudentSubmission` não interrompe a importação: a tarefa fica `pending` e o sincronismo registra um aviso sanitizado.

## API interna do EduTrack

Todas as rotas exigem a sessão atual do EduTrack, exceto que o callback também valida o `state` assinado vinculado ao mesmo usuário.

- `GET /api/integrations/classroom` — retorna disponibilidade, conexão, último sincronismo e último código de erro.
- `GET /api/integrations/classroom/authorize` — cria estado/PKCE e redireciona ao Google.
- `GET /api/integrations/classroom/callback` — troca o código, cifra o refresh token e redireciona à tela de integrações.
- `POST /api/integrations/classroom/sync` — executa sincronização idempotente e retorna contagens e avisos.
- `DELETE /api/integrations/classroom` — exclui credenciais e vínculos; disciplinas e tarefas já importadas permanecem locais.

O frontend nunca chama a API Google diretamente.

## Componentes do backend

- `app/integrations/google_classroom/client.py`: constrói URLs OAuth, troca/renova tokens e encapsula paginação da API REST.
- `app/integrations/google_classroom/crypto.py`: cifra e decifra somente refresh tokens.
- `app/integrations/google_classroom/sync.py`: aplica as regras idempotentes de importação em uma transação.
- `app/models/classroom.py`: modelos de conexão e vínculos.
- `app/repositories/classroom.py`: consultas e upserts dos três modelos.
- `app/schemas/classroom.py`: contratos da API interna e resultado do sincronismo.
- `app/api/classroom.py`: rotas, cookies temporários, redirecionamentos e tradução de erros.

O cliente Google será injetável no serviço de sincronização para que os testes usem um cliente determinístico sem rede.

## Tratamento de erros

- `access_denied`: o usuário cancelou; retornar à tela sem criar conexão.
- `admin_policy_enforced` ou bloqueio equivalente: mostrar que a instituição precisa liberar o aplicativo.
- `invalid_grant`: apagar o refresh token inválido, manter dados importados e exigir reconexão.
- `429` e `5xx`: não remover conexão nem dados; registrar código sanitizado e permitir nova tentativa.
- resposta parcial ou item malformado: ignorar apenas o item, contabilizar aviso e continuar os demais.
- falha de banco: reverter a transação completa do sincronismo para impedir importação parcial inconsistente.

Tokens, códigos OAuth, respostas completas do provedor e dados pessoais não serão gravados em logs.

## Supabase e segurança do banco

A integração usa a conexão PostgreSQL privada já consumida pelo SQLAlchemy; não usa `supabase-js`, chave `anon` ou `service_role` no navegador. O schema `private` evita exposição automática pela Data API. A migração habilitará RLS nas novas tabelas e revogará privilégios de `anon` e `authenticated` somente quando esses papéis existirem, mantendo compatibilidade com o PostgreSQL portátil local.

O changelog do Supabase consultado em 3 de setembro de 2026 informa que novas tabelas podem não ser expostas automaticamente à Data API. O projeto ainda aplicará isolamento explícito em vez de depender dessa configuração variável.

## Testes e critérios de aceite

### Testes unitários

- cifrar e decifrar refresh token sem persistir texto puro;
- rejeitar chave Fernet inválida;
- gerar e validar estado OAuth expirável e vinculado ao usuário;
- mapear estados `TURNED_IN`, `RETURNED`, `RECLAIMED`, `NEW` e `CREATED`;
- ignorar atividade sem prazo com contagem correta;
- preservar `in_progress` para entrega ainda não enviada.

### Testes de repositório e API

- aplicar e reverter a migração no PostgreSQL de teste;
- impedir vínculos duplicados no mesmo curso e atividade;
- exigir sessão nas rotas;
- não disponibilizar autorização quando a configuração estiver desabilitada;
- validar callback com `state` incorreto, expirado ou pertencente a outro usuário;
- desconectar sem excluir disciplinas e tarefas;
- converter erros Google em códigos internos sem vazar tokens.

### Teste de sincronização

Com um cliente Google determinístico, executar dois sincronismos idênticos e comprovar que o segundo cria zero registros. Alterar depois prazo e estado no fixture e comprovar atualização da tarefa vinculada.

### Teste de navegador

- abrir Integrações;
- verificar estado desconectado;
- simular retorno conectado sem acessar o Google real;
- iniciar sincronização;
- visualizar resumo, selo Google Classroom e link externo seguro;
- validar layout desktop e mobile sem rolagem horizontal.

### Verificação final

- suíte completa `pytest`;
- Ruff em `app`, `scripts`, `tests` e `alembic`;
- `alembic upgrade head`, `alembic downgrade -1` e novo `upgrade head` no banco de teste;
- inspeção de que `.env`, client secret, refresh token e chave de cifragem não aparecem no diff;
- teste real opcional com conta Google pessoal cadastrada como usuário de teste no Google Cloud Console.

## Pré-requisitos externos

Antes do teste real será necessário criar ou selecionar um projeto no Google Cloud, habilitar a Google Classroom API, configurar a tela de consentimento, cadastrar o usuário de teste e adicionar as URIs de redirecionamento local e de produção. Uma conta institucional pode continuar bloqueada até o administrador da escola aprovar o aplicativo; isso não impede testes com uma conta pessoal.

## Referências oficiais

- [Google Classroom API](https://developers.google.com/workspace/classroom/reference/rest)
- [Escopos OAuth do Classroom](https://developers.google.com/workspace/classroom/guides/auth)
- [CourseWork](https://developers.google.com/workspace/classroom/reference/rest/v1/courses.courseWork)
- [StudentSubmissions](https://developers.google.com/workspace/classroom/reference/rest/v1/courses.courseWork.studentSubmissions)
- [Controle administrativo de aplicativos Workspace](https://support.google.com/a/answer/7281227)
- [Supabase changelog](https://supabase.com/changelog.md)

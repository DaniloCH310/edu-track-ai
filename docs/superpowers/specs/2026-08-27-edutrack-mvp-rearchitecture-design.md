# EduTrack AI MVP - Reestruturação Full-Stack

**Data:** 27 de agosto de 2026
**Status:** aprovado em conversa, aguardando revisão do documento
**Escopo:** MVP web responsivo

## 1. Objetivo

Reestruturar o protótipo Streamlit do EduTrack AI como uma aplicação web full-stack com frontend em HTML, CSS e JavaScript, backend FastAPI e persistência PostgreSQL. O MVP permitirá autenticação, recuperação real de senha por Gmail, gerenciamento de disciplinas e tarefas e acompanhamento do progresso acadêmico em um dashboard.

## 2. Escopo do MVP

### Incluído

- Cadastro, login e logout de usuário.
- Recuperação de senha por e-mail usando Gmail SMTP.
- Isolamento completo dos dados por usuário.
- CRUD de disciplinas.
- CRUD de tarefas vinculadas a disciplinas.
- Alteração rápida do status de uma tarefa.
- Busca, filtros e ordenação de tarefas.
- Dashboard com métricas gerais, progresso por disciplina, próximas entregas e tarefas atrasadas.
- Tema claro/escuro e interface responsiva.
- Seed opcional com conta e dados de demonstração.
- Execução local sem privilégios administrativos, usando PostgreSQL portátil e scripts PowerShell.

### Fora do MVP

- Cronômetro e registro de tempo estimado/real.
- Insights com IA generativa.
- Métricas avançadas ou previsão de conclusão.
- Relatórios semanais em PDF.
- Notificações push.
- Integração com Xano, FlutterFlow ou Streamlit.

## 3. Arquitetura

O FastAPI será o único processo web da aplicação. Ele servirá os arquivos estáticos do frontend e exporá a API REST sob `/api`. O navegador consumirá a API usando JSON. PostgreSQL armazenará todos os dados persistentes. SQLAlchemy fará o mapeamento relacional e Alembic controlará as migrações.

```text
Navegador
  -> HTML + CSS + JavaScript modular
  -> JSON / REST
FastAPI
  -> rotas e validação
  -> autenticação e autorização
  -> serviços de domínio
  -> repositórios SQLAlchemy
PostgreSQL
```

### Organização prevista

```text
app/
  api/
  core/
  models/
  repositories/
  schemas/
  services/
  static/
    css/
    js/
    index.html
  main.py
alembic/
scripts/
  setup-postgres.ps1
  start-postgres.ps1
  stop-postgres.ps1
  start-app.ps1
tests/
.env.example
```

Os módulos terão responsabilidades restritas. Rotas HTTP não conterão consultas SQL ou regras complexas. Serviços coordenarão as regras de negócio, e repositórios encapsularão a persistência.

## 4. Modelo de dados

### users

- `id`: UUID, chave primária.
- `name`: nome de exibição.
- `email`: único, normalizado e indexado.
- `password_hash`: hash seguro da senha.
- `is_active`: habilita ou bloqueia acesso.
- `created_at` e `updated_at`: timestamps com fuso horário.

### password_reset_tokens

- `id`: UUID, chave primária.
- `user_id`: referência a `users`.
- `token_hash`: hash do token enviado por e-mail; o token em texto puro não será persistido.
- `expires_at`: validade curta.
- `used_at`: preenchido no primeiro uso.
- `created_at`: timestamp com fuso horário.

### subjects

- `id`: UUID, chave primária.
- `user_id`: proprietário e chave estrangeira para `users`.
- `name`: nome da disciplina.
- `professor`: nome opcional.
- `workload_hours`: carga horária positiva.
- `description`: descrição opcional.
- `period`: período acadêmico opcional.
- `color`: cor hexadecimal validada.
- `start_date` e `end_date`: datas opcionais, com fim igual ou posterior ao início.
- `created_at` e `updated_at`: timestamps com fuso horário.

### academic_tasks

- `id`: UUID, chave primária.
- `subject_id`: chave estrangeira para `subjects` com exclusão em cascata.
- `title`: título obrigatório.
- `description`: descrição opcional.
- `due_date`: data prevista.
- `status`: `pending`, `in_progress` ou `completed`.
- `completed_at`: preenchido quando o status passa a concluído.
- `created_at` e `updated_at`: timestamps com fuso horário.

O acesso a uma tarefa será autorizado por meio da disciplina e do proprietário autenticado. Nenhum identificador fornecido pelo cliente permitirá atravessar a fronteira entre usuários.

## 5. Contratos da API

### Autenticação

```text
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me
POST /api/auth/forgot-password
POST /api/auth/reset-password
```

O login emitirá um JWT de curta duração em cookie `HttpOnly`, `SameSite=Lax` e `Secure` quando o ambiente for produção. Logout removerá o cookie. A recuperação sempre retornará uma resposta neutra, exista ou não uma conta com o e-mail informado.

### Disciplinas

```text
GET    /api/subjects
POST   /api/subjects
GET    /api/subjects/{id}
PUT    /api/subjects/{id}
DELETE /api/subjects/{id}
```

A exclusão removerá as tarefas da disciplina. A interface exigirá confirmação explícita e informará essa consequência.

### Tarefas

```text
GET    /api/tasks
POST   /api/tasks
GET    /api/tasks/{id}
PUT    /api/tasks/{id}
PATCH  /api/tasks/{id}/status
DELETE /api/tasks/{id}
```

`GET /api/tasks` aceitará busca textual, status, disciplina e ordenação por prazo. Todos os filtros serão aplicados apenas sobre dados do usuário autenticado.

### Dashboard

```text
GET /api/dashboard
```

A resposta incluirá total de tarefas, total concluído, progresso geral, entregas nos próximos três dias, tarefas atrasadas, progresso por disciplina e uma lista limitada de próximas entregas.

### Formato de erro

Erros esperados usarão um envelope estável:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Revise os campos informados.",
    "fields": {}
  }
}
```

Mensagens internas, consultas e exceções não serão expostas ao cliente.

## 6. Interface e experiência

### Identidade

A interface preservará a identidade do protótipo atual: roxo como cor principal, verde e laranja como apoio semântico, superfícies limpas e linguagem acadêmica acolhedora. O tema escuro manterá o mesmo sistema de cores com contraste adequado.

### Telas

- **Entrar/criar conta:** formulário central, alternância entre modos e acesso à recuperação de senha.
- **Recuperar/redefinir senha:** confirmação neutra de envio e formulário de nova senha aberto pelo link recebido.
- **Dashboard:** saudação, quatro métricas, gráfico de progresso, próximas entregas e resumo das disciplinas.
- **Disciplinas:** lista responsiva com progresso, professor, carga horária e período; inclusão e edição em modal.
- **Tarefas:** busca, filtros por status e disciplina, ordenação por prazo, inclusão/edição em modal e alteração rápida de status.

### Navegação e responsividade

O desktop usará sidebar com as áreas Dashboard, Disciplinas e Tarefas. Em telas pequenas, a navegação será compactada. Listas serão reorganizadas verticalmente no celular, sem tabelas comprimidas ou rolagem horizontal como fluxo principal.

### Estados de interface

Toda operação assíncrona terá estado de carregamento. Haverá estados vazios com ação recomendada, notificações de sucesso, erros traduzidos para português, confirmação para exclusões e prevenção de submissão duplicada. Controles terão foco visível, rótulos acessíveis e operação por teclado.

## 7. Segurança

- Senhas serão processadas por algoritmo de hash de senha resistente e nunca registradas em logs.
- O JWT será armazenado somente em cookie `HttpOnly`.
- Cookies de produção usarão `Secure`; o ambiente local permitirá HTTP.
- Tokens de recuperação serão aleatórios, de uso único, expirarão e serão persistidos apenas como hash.
- Rotas de login e recuperação terão limitação básica de tentativas por origem.
- Operações de disciplina e tarefa sempre filtrarão pelo usuário autenticado.
- Segredos de banco, JWT e Gmail serão lidos de variáveis de ambiente.
- `.env` não será versionado; `.env.example` conterá apenas nomes e exemplos seguros.
- O Gmail será configurado por endereço remetente e senha de aplicativo, nunca pela senha normal da conta.

## 8. Gmail e recuperação de senha

O serviço SMTP usará host `smtp.gmail.com`, porta 587 e STARTTLS. O e-mail conterá um link para a página de redefinição com token aleatório e validade configurável. Em desenvolvimento, falhas SMTP serão registradas sem revelar credenciais ou o token completo. A API não confirmará se um e-mail está cadastrado.

## 9. PostgreSQL portátil e operação local

O ambiente não possui Docker nem privilégios administrativos. `scripts/setup-postgres.ps1` baixará o arquivo ZIP de binários PostgreSQL 16 para Windows x86-64 indicado pela página oficial de downloads do PostgreSQL, validará que o arquivo é um ZIP íntegro, extrairá os binários para `.tools/postgresql`, inicializará os clusters locais em `.data/postgresql/dev` e `.data/postgresql/test` e criará os bancos da aplicação e de testes. Esses diretórios serão ignorados pelo Git.

`scripts/start-postgres.ps1` iniciará os clusters com `pg_ctl` em portas locais distintas, sem registrar serviço do Windows. `scripts/stop-postgres.ps1` fará o encerramento controlado. `scripts/start-app.ps1` verificará o banco, aplicará `alembic upgrade head` e iniciará o Uvicorn.

O fluxo principal será:

```powershell
Copy-Item .env.example .env
.\scripts\setup-postgres.ps1
.\scripts\start-app.ps1
```

Um comando separado criará a conta e os dados de demonstração de forma idempotente. As credenciais de demonstração serão configuráveis e destinadas apenas ao ambiente local.

## 10. Testes e critérios de aceitação

### Backend

- Cadastro cria usuário e sessão autenticada.
- E-mail duplicado é rejeitado sem diferenças que facilitem enumeração indevida.
- Login correto autentica; senha incorreta não autentica.
- Logout invalida a sessão do navegador.
- Recuperação cria token válido, envia e-mail e permite uma única redefinição dentro do prazo.
- Usuário não lê nem modifica disciplinas ou tarefas de outro usuário.
- CRUD de disciplinas respeita validações e exclusão em cascata.
- CRUD de tarefas respeita vínculo, status e filtros.
- Dashboard calcula progresso e prazos corretamente.

### Frontend

- Usuário percorre cadastro/login, cria disciplina, cria tarefa, conclui tarefa e vê o dashboard atualizado.
- Formulários apresentam validação e feedback compreensíveis.
- Filtros e busca atualizam a lista de tarefas.
- Tema e navegação funcionam em desktop e celular.
- Fluxos principais são utilizáveis por teclado e não apresentam overflow horizontal em viewport móvel.

### Infraestrutura

- Migrações partem de um PostgreSQL vazio.
- Os scripts instalam, inicializam, iniciam e encerram PostgreSQL sem acesso administrativo.
- O banco de desenvolvimento e o banco de testes usam clusters e portas separados.
- Seed pode ser executado mais de uma vez sem duplicar dados.
- Testes usam um banco separado do ambiente de desenvolvimento.

## 11. Estratégia de implementação

A implementação seguirá testes primeiro nas regras e contratos críticos. A ordem será: fundação e banco, autenticação, disciplinas, tarefas, dashboard, frontend, recuperação por Gmail, PostgreSQL portátil/seed e validação final. O protótipo Streamlit será preservado durante a construção e removido ou arquivado somente quando a nova aplicação estiver validada.

## 12. Decisões fechadas

- Escopo: MVP.
- Backend: FastAPI.
- Frontend: HTML, CSS e JavaScript sem framework.
- Persistência: PostgreSQL.
- Execução local: PostgreSQL portátil e scripts PowerShell, sem privilégios administrativos.
- E-mail: Gmail SMTP real com credenciais por `.env`.
- Arquitetura: FastAPI serve API e frontend estático no mesmo processo.
- Visual: evolução da identidade atual do EduTrack.
- Demonstração: conta e dados de seed opcionais.

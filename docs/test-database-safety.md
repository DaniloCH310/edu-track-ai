# Proteção do banco de testes

O pytest nunca deve usar o banco de desenvolvimento ou produção. A autorização
fica centralizada em `app/core/database_safety.py`, sem depender de `TESTING=true`.

## Política

- `ENVIRONMENT` precisa ser exatamente `test`. O bootstrap do pytest define esse
  valor quando ausente e recusa valores herdados como `development` ou `production`.
- A URL precisa usar `postgresql+psycopg`, host literal `127.0.0.1`, usuário
  `edutrack` e banco exatamente `edutrack_test`, sem parâmetros de conexão extras.
- A porta local é exclusivamente `54330`. Dentro do GitHub Actions, é `5432`.
  A variável do CI apenas seleciona a porta; não libera outros hosts, bancos ou usuários.
- `DATABASE_URL` herdada é validada, nunca substituída silenciosamente. Uma
  `TEST_DATABASE_URL` explicitamente exportada também deve ser válida e coincidir.
- Antes de disponibilizar cada conexão de teste, uma consulta somente leitura
  confere banco, usuário atual, usuário da sessão, porta real e comentário do banco.
- O comentário deve ser exatamente `edutrack:disposable-test-database:v1`.
  Essa marca é uma autorização administrativa de uso descartável, não uma senha.
- A limpeza repete a autorização na mesma conexão/transação antes de cada
  `TRUNCATE`, tanto na preparação quanto no encerramento da fixture.
- Migrações com `ENVIRONMENT=test` validam a conexão antes de executar Alembic.
  Migrações offline nesse modo são recusadas porque não permitem verificar o banco.

## Provisionamento e bancos existentes

O instalador marca somente um `edutrack_test` novo que acabou de criar na porta
54330. Executar o instalador novamente **não autoriza um banco já existente**.
O CI marca apenas o banco criado pelo serviço PostgreSQL descartável do próprio job,
antes das migrações. Nenhum destino é selecionado pela URL da aplicação nesse passo.

Para uma instalação antiga, pare antes de rodar testes dependentes do banco.
Verifique com o responsável que o cluster e o banco são exclusivos para testes,
não contêm dados a preservar e não são um túnel/proxy de outro ambiente.
Somente após essa verificação, um administrador pode executar no banco dedicado:

```sql
COMMENT ON DATABASE edutrack_test IS 'edutrack:disposable-test-database:v1';
```

Não copie essa marca para backups de produção, não a aplique automaticamente
quando uma validação falhar e não use nomes de teste para hospedar dados reais.
A proteção não é uma fronteira contra um administrador que possa alterar o código,
a configuração do servidor ou o comentário do banco.

## Verificações seguras sem banco

```powershell
.\.venv\Scripts\python.exe -B -m pytest tests/unit --ignore=tests/unit/test_classroom_sync.py -p no:cacheprovider -q
.\.venv\Scripts\python.exe -B -m ruff check --no-cache app scripts tests alembic
```

Os testes de `test_database_safety.py` usam conexões simuladas. Não executam
`TRUNCATE`, migrações ou autorizações em bancos reais. A suíte completa só deve
ser iniciada depois da conferência do banco dedicado e das migrações em modo teste.

## Inventário de operações

- `tests/conftest.py`: limpeza antes/depois das fixtures; agora delega a
  `clean_test_database()`, único `TRUNCATE` executável da infraestrutura de testes.
- Testes de API/E2E: exclusões CRUD e cascatas; dependem de `database_cleaner`,
  portanto não chegam ao corpo do teste sem autorização. A conexão da aplicação
  também é validada em `app/core/database.py` quando o ambiente é `test`.
- `alembic/versions/*`: os downgrades contêm remoção de tabelas, índices, colunas,
  tipos e do schema `private`. O `alembic/env.py` protege migrações no ambiente
  `test`; migrações normais de desenvolvimento/produção mantêm seu fluxo existente.
  Esta proteção de testes não é uma autorização para executar downgrades fora dele.
- `scripts/setup-postgres.ps1`: cria clusters/bancos ausentes e remove somente
  o arquivo temporário de senha; não apaga ou recria bancos existentes.
- Repositórios da aplicação: exclusões de entidades individuais e cascatas são
  funcionalidades de negócio existentes, preservadas nesta correção.

Não foram encontrados `DELETE FROM` em massa, `drop_all()` ou recriação de schemas
como mecanismo adicional de limpeza da suíte.

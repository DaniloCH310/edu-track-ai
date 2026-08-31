# Operação em produção

## Arquitetura

O Render executa uma única instância do FastAPI, que serve o frontend e a API. O
PostgreSQL é o projeto Supabase `lggbcaexepmjdziejnli`; a aplicação não usa a
Data API do Supabase nem chaves `anon` ou `service_role` no navegador.

## Publicar no Render

1. Entre no [Render Dashboard](https://dashboard.render.com/) e conecte a conta
   GitHub que tem acesso a `DaniloCH310/edu-track-ai-evandro`.
2. Escolha **New +** > **Blueprint**, selecione o repositório e a branch `main`.
   O Render detectará `render.yaml`.
3. No Supabase, abra o projeto, clique em **Connect** e copie a string do
   **Session pooler**. Esse é o modo apropriado para um backend persistente
   acessado por rede IPv4. Troque o prefixo `postgresql://` por
   `postgresql+psycopg://` e acrescente `?sslmode=require`.
4. Preencha os campos secretos solicitados pelo Blueprint:

   - `DATABASE_URL`: a URL do passo anterior;
   - `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`: a conta Gmail e a
     senha de aplicativo já configurada para envio;
   - `FRONTEND_URL`: a URL HTTPS do serviço Render, por exemplo
     `https://edutrack-ai.onrender.com`.

   `JWT_SECRET` é gerado pelo Render. Nunca coloque esses valores em arquivos
   versionados, no frontend ou em mensagens públicas.
5. Crie o Blueprint. A cada deploy, o Render instala o pacote, executa
   `alembic upgrade head` antes de iniciar a aplicação e consulta
   `/api/health` como health check.
6. Após o primeiro deploy, abra `https://SEU-SERVICO.onrender.com/api/health`.
   A resposta esperada é `{"status":"ok"}`. Em seguida, faça um cadastro de
   teste, login e logout pelo navegador.

Para trocar o domínio depois, atualize `FRONTEND_URL` no painel do Render e
faça novo deploy. Em produção, a aplicação recusa subir se `COOKIE_SECURE` não
for `true` ou se `FRONTEND_URL` não usar HTTPS.

## Integração contínua

O arquivo `.github/workflows/ci.yml` executa em cada pull request e push para
`main`:

1. cria um PostgreSQL 16 temporário;
2. aplica as migrações Alembic;
3. executa testes de API, integração e unidade;
4. executa Ruff.

Os testes E2E de navegador continuam disponíveis localmente e não fazem parte
desse job Linux, pois a suíte local usa o Microsoft Edge instalado no Windows.
O Render só fará auto-deploy quando as verificações do GitHub passarem.

## Backup e restauração

O Supabase oferece backups diários em **Database > Backups**. Verifique no
painel se há um backup recente antes de colocar dados reais em produção. Caso o
plano permita, ative **Point in Time Recovery (PITR)** para diminuir a perda
potencial de dados entre backups diários.

Antes de restaurar:

1. avise os usuários e coloque o serviço Render em manutenção ou pause o deploy;
2. escolha, em **Database > Backups**, o ponto imediatamente anterior ao erro;
3. confirme a restauração no Supabase e espere o projeto voltar a ficar
   acessível;
4. execute a verificação de saúde e teste login, criação de disciplina e tarefa;
5. se existirem roles PostgreSQL personalizados, redefina suas senhas, pois os
   backups diários não preservam essas senhas.

Uma restauração deixa o projeto temporariamente indisponível. Não execute
restaurações em produção sem escolher conscientemente o ponto de recuperação.

## Reversão de aplicação

No Render, abra o histórico de deploys do serviço e use **Rollback** para a
última versão saudável. Isso reverte somente o código; o schema é migrado para
frente e não deve ser revertido manualmente sem um plano de migração próprio.

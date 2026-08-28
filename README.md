# EduTrack AI

MVP web para organização acadêmica, com frontend em HTML/CSS/JavaScript,
API FastAPI e PostgreSQL. O estudante pode cadastrar disciplinas, planejar
tarefas, filtrar entregas, acompanhar progresso e recuperar a senha por Gmail.

## Requisitos

- Windows 10/11;
- Python 3.12 ou superior;
- conexão com a internet apenas na primeira configuração;
- não é necessário acesso administrativo.

O PostgreSQL 16.15 é baixado como pacote portátil oficial e permanece dentro
do projeto. A origem do pacote é a página de downloads para Windows do
[PostgreSQL](https://www.postgresql.org/download/windows/), com binários da EDB.

## Primeira configuração

Abra o PowerShell na pasta do projeto e execute:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env
.\scripts\setup-postgres.ps1
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m scripts.seed
```

O script cria os bancos `edutrack` em `127.0.0.1:54329` e `edutrack_test` em
`127.0.0.1:54330`. Em caminhos com caracteres acentuados, ele cria uma unidade
virtual de usuário (por exemplo, `Z:`), sem mover arquivos nem pedir acesso
administrativo.

## Iniciar manualmente

Sempre que quiser usar o EduTrack:

```powershell
cd "C:\Users\DaniloChavesdeSá\Desktop\edu-track-ai-evandro-main"
.\scripts\start-app.ps1
```

Abra [http://127.0.0.1:8000](http://127.0.0.1:8000). O script inicia o banco,
aplica migrações e sobe o FastAPI. Para encerrar a aplicação, pressione `Ctrl+C`.
Para encerrar também o PostgreSQL:

```powershell
.\scripts\stop-postgres.ps1 -Cluster All
```

Controle isolado dos clusters:

```powershell
.\scripts\start-postgres.ps1 -Cluster Dev
.\scripts\start-postgres.ps1 -Cluster Test
.\scripts\stop-postgres.ps1 -Cluster Dev
```

## Conta demonstrativa

O comando `python -m scripts.seed` é idempotente e prepara:

- e-mail: `demo@example.com`;
- senha inicial: `Demo-Segura-123`;
- três disciplinas e cinco tarefas de exemplo.

Altere `DEMO_EMAIL` e `DEMO_PASSWORD` no `.env` antes do seed se preferir outras
credenciais. A senha nunca é impressa pelo comando.

## Configurar recuperação real pelo Gmail

1. Ative a verificação em duas etapas na conta Google remetente.
2. No gerenciamento da Conta Google, crie uma **Senha de app**.
3. Edite o `.env`:

```dotenv
SMTP_USERNAME=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-de-app
SMTP_FROM_EMAIL=seu-email@gmail.com
```

Não use a senha normal do Gmail e não compartilhe o `.env`. O serviço usa
`smtp.gmail.com:587`, STARTTLS e resposta neutra para impedir descoberta de
contas cadastradas.

## Testes e qualidade

```powershell
.\scripts\start-postgres.ps1 -Cluster Test
.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider
.\.venv\Scripts\python.exe -m ruff check --no-cache app scripts tests alembic
```

Os testes de navegador usam o Microsoft Edge instalado no Windows e cobrem
cadastro/login, responsividade, tema e o fluxo disciplina → tarefa → dashboard.

## Estrutura e dados locais

- `app/static/`: frontend HTML/CSS/JavaScript;
- `app/api/`, `app/services/`, `app/repositories/`: API e regras de negócio;
- `alembic/`: versionamento do schema;
- `.tools/`: binários portáteis do PostgreSQL;
- `.data/`: clusters e dados locais;
- `app.py`: protótipo Streamlit legado, preservado apenas como referência.

`.tools`, `.data`, `.env` e `.venv` são ignorados pelo Git. Só remova `.data`
quando quiser descartar deliberadamente todos os dados locais.

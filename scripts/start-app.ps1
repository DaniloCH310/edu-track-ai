[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $projectRoot '.env'
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $envFile)) {
    throw 'Arquivo .env não encontrado. Copie .env.example para .env e configure o Gmail.'
}
if (-not (Test-Path -LiteralPath $python)) {
    throw 'Ambiente virtual não encontrado. Crie .venv e instale o projeto.'
}

& (Join-Path $PSScriptRoot 'start-postgres.ps1') -Cluster Dev
Push-Location $projectRoot
try {
    & $python -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) {
        throw 'A migração do banco falhou.'
    }
    & $python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
} finally {
    Pop-Location
}
